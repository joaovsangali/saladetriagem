# app/intake/routes.py
# Alterações mínimas para preparar o motor para “nichos futuros”:
# - Usa SEMPRE o schema do link (form_schema) como fonte de crime_types/labels/questions
# - Não depende mais de CRIME_SCHEMAS para coletar perguntas no submit
# - Garante defaults úteis no schema (domain/schema_version) sem quebrar nada

import io
import logging
import uuid
from datetime import datetime, timezone
from flask import render_template, redirect, url_for, flash, request, current_app
from app.intake import intake_bp
from app.extensions import limiter
from app.models import IntakeLink, DashboardSession
from app.store import submission_store, Submission
from app.schemas.crime_types import CRIME_SCHEMAS

logger = logging.getLogger(__name__)

_DEFAULT_MAX_PHOTO_SIZE_MB = 3


def _strip_exif(image_bytes: bytes) -> bytes:
    try:
        from PIL import Image
        img = Image.open(io.BytesIO(image_bytes))
        output = io.BytesIO()
        # Convert to RGB to drop EXIF and extra metadata
        rgb = img.convert("RGB")
        rgb.save(output, format="JPEG", quality=85)
        return output.getvalue()
    except Exception:
        return image_bytes


@intake_bp.route("/t/<token>")
@limiter.limit("20 per minute")
def form(token):
    link = IntakeLink.query.filter_by(token=token, is_active=True).first_or_404()
    session = DashboardSession.query.get(link.dashboard_id)

    if not session or not session.is_active or session.is_expired:
        return render_template("intake/expired.html")

    schema = link.form_schema or {}

    # Defaults "future-proof" (não quebra nada hoje)
    schema.setdefault("domain", "police")
    schema.setdefault("schema_version", 1)

    # Tipos/labels/questions preferencialmente vêm do schema do link
    crime_types = schema.get("crime_types")
    if not crime_types:
        crime_types = list(CRIME_SCHEMAS.keys())

    # Labels: primeiro tenta do schema, senão cai no CRIME_SCHEMAS (fallback)
    schema_labels = schema.get("crime_labels") or {}
    crime_labels = {}
    for k in crime_types:
        crime_labels[k] = schema_labels.get(k) or CRIME_SCHEMAS.get(k, {}).get("label", k)

    # Questions: primeiro tenta do schema, senão cai no CRIME_SCHEMAS (fallback)
    questions_by_crime = schema.get("questions_by_crime")
    if not isinstance(questions_by_crime, dict) or not questions_by_crime:
        questions_by_crime = {
            k: CRIME_SCHEMAS[k]["questions"]
            for k in crime_types
            if k in CRIME_SCHEMAS and "questions" in CRIME_SCHEMAS[k]
        }

    return render_template(
        "intake/form.html",
        token=token,
        schema=schema,
        crime_types=crime_types,
        crime_labels=crime_labels,
        questions_by_crime=questions_by_crime,
    )


@intake_bp.route("/t/<token>/submit", methods=["POST"])
@limiter.limit("5 per minute")
def submit(token):
    link = IntakeLink.query.filter_by(token=token, is_active=True).first_or_404()
    session = DashboardSession.query.get(link.dashboard_id)

    if not session or not session.is_active or session.is_expired:
        return render_template("intake/expired.html")

    # Enforce plan limit: max submissions per session
    owner = session.owner
    if owner:
        limits = owner.get_current_plan_limits()
        current_count = submission_store.count_for_dashboard(session.id)
        if current_count >= limits['max_submissions_per_session']:
            return render_template("intake/expired.html")

    schema = link.form_schema or {}

    # Defaults "future-proof"
    schema.setdefault("domain", "police")
    schema.setdefault("schema_version", 1)

    limits = schema.get("limits", {})
    max_photos = limits.get("max_photos", 3)
    max_photo_size = limits.get("max_photo_size_mb", _DEFAULT_MAX_PHOTO_SIZE_MB) * 1024 * 1024

    crime_type = request.form.get("crime_type", "outros")
    guest_name = request.form.get("guest_name", "").strip()

    if not guest_name:
        flash("Nome é obrigatório.", "danger")
        return redirect(url_for("intake.form", token=token))

    dob = request.form.get("dob", "").strip() or None
    rg = request.form.get("rg", "").strip() or None
    raw_cpf = request.form.get("cpf", "").strip() or None
    from app.utils.validators import normalize_cpf
    cpf = normalize_cpf(raw_cpf) if raw_cpf else None
    address = request.form.get("address", "").strip() or None
    narrative = request.form.get("narrative", "").strip() or None
    phone = request.form.get("phone", "").strip() or None
    email = request.form.get("email", "").strip() or None

    # Policial Militar fields
    policial_militar = request.form.get("policial_militar", "") == "sim"
    pm_re = request.form.get("pm_re", "").strip() or None if policial_militar else None
    pm_batalhao = request.form.get("pm_batalhao", "").strip() or None if policial_militar else None
    pm_companhia = request.form.get("pm_companhia", "").strip() or None if policial_militar else None

    # Vítimas (PM)
    vitimas = []
    if policial_militar:
        from app.utils.validators import normalize_cpf as _normalize_cpf
        for i in range(1, 6):
            nome_vitima = request.form.get(f"vitima__{i}__nome", "").strip()
            if nome_vitima:
                raw_cpf_vitima = request.form.get(f"vitima__{i}__cpf", "").strip() or None
                vitimas.append({
                    "nome": nome_vitima,
                    "data_nascimento": request.form.get(f"vitima__{i}__data_nascimento", "").strip() or None,
                    "rg": request.form.get(f"vitima__{i}__rg", "").strip() or None,
                    "cpf": _normalize_cpf(raw_cpf_vitima) if raw_cpf_vitima else None,
                    "email": request.form.get(f"vitima__{i}__email", "").strip() or None,
                    "endereco": request.form.get(f"vitima__{i}__endereco", "").strip() or None,
                })

    # Collect answers: usa o schema do link (não CRIME_SCHEMAS global)
    questions_by_crime = schema.get("questions_by_crime", {})
    questions = questions_by_crime.get(crime_type, [])

    answers = {}

    for q in questions:
        qid = q.get("id")
        qtype = q.get("type", "text")

        if not qid:
            continue

        # group (lista de objetos repetíveis)
        if qtype == "group":
            items = []
            fields = q.get("fields", [])
            max_items = int(q.get("max_items", 5))

            for i in range(max_items):
                obj = {}
                has_any = False

                for f in fields:
                    fid = f.get("id")
                    ftype = f.get("type", "text")
                    if not fid:
                        continue

                    raw = request.form.get(f"q_{qid}__{i}__{fid}", "").strip()

                    if ftype == "boolean":
                        if raw == "":
                            obj[fid] = None
                        else:
                            obj[fid] = raw.lower() in ("1", "true", "yes", "sim", "on")
                            has_any = True
                    else:
                        if raw != "":
                            obj[fid] = raw
                            has_any = True
                        else:
                            obj[fid] = None

                if has_any:
                    items.append(obj)

            answers[qid] = items
            continue

        # checkbox_group
        if qtype == "checkbox_group":
            values = [v.strip() for v in request.form.getlist(f"q_{qid}") if v.strip()]
            answers[qid] = values if values else []
            continue

        # boolean padrão
        val = request.form.get(f"q_{qid}", "").strip()

        if qtype == "boolean":
            if val == "":
                answers[qid] = None
            else:
                answers[qid] = val.lower() in ("1", "true", "yes", "sim", "on")
        else:
            answers[qid] = val if val else None

    # process photos and PDFs
    photos = []
    photo_keys = []
    files = request.files.getlist("photos")
    allowed_mime = {"image/jpeg", "image/png", "image/gif", "application/pdf"}
    # Only externalise photos to storage when the backend is S3.
    # For local mode the existing in-memory / Redis path is preserved so that
    # the API can serve photos directly without an extra disk read.
    use_external_storage = (
        current_app.config.get("STORAGE_BACKEND", "local") == "s3"
        and getattr(current_app, "photo_storage", None) is not None
    )
    storage = getattr(current_app, "photo_storage", None) if use_external_storage else None
    for f in files[:max_photos]:
        if not f or not f.filename:
            continue
        if f.mimetype not in allowed_mime:
            continue
        data = f.read(max_photo_size + 1)
        if len(data) > max_photo_size:
            continue
        # Only strip EXIF from images, not PDFs
        if f.mimetype == "application/pdf":
            cleaned = data
        else:
            cleaned = _strip_exif(data)
        if storage is not None:
            # Persist to S3 and keep only the key in memory.  On failure fall
            # back to in-memory bytes so a transient S3 error never blocks a
            # submission.
            try:
                key = storage.save(cleaned, f.filename or "photo.jpg")
                photo_keys.append(key)
            except Exception as exc:
                logger.warning("S3 photo upload failed, keeping in memory: %s", exc)
                photos.append(cleaned)
        else:
            photos.append(cleaned)

    # Incorporate PM and victim data into answers
    if policial_militar:
        pm_data = {
            "policial_militar": True,
            "pm_re": pm_re,
            "pm_batalhao": pm_batalhao,
            "pm_companhia": pm_companhia,
        }
        if vitimas:
            pm_data["vitimas"] = vitimas
        answers["_pm_info"] = pm_data

    if email:
        answers["_email"] = email

    sub = Submission(
        submission_id=str(uuid.uuid4()),
        dashboard_id=session.id,
        guest_name=guest_name,
        dob=dob,
        rg=rg,
        cpf=cpf,
        phone=phone,
        address=address,
        answers=answers,
        narrative=narrative,
        crime_type=crime_type,
        photos=photos,
        photo_keys=photo_keys,
        received_at=datetime.now(timezone.utc),
    )

    # Duplicate check — same name or same RG within this dashboard
    if submission_store.is_duplicate(sub):
        flash(
            "Já existe um registro com esse nome ou RG nesta triagem. "
            "Se necessário, informe o policial.",
            "warning",
        )
        return redirect(url_for("intake.form", token=token))

    submission_store.add(sub)

    # Track usage for plan enforcement
    if owner:
        from app.decorators import increment_submissions
        increment_submissions(owner.id)

    return redirect(url_for("intake.ok", token=token))


@intake_bp.route("/t/<token>/ok")
def ok(token):
    return render_template("intake/ok.html")