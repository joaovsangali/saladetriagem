import io
import uuid
from datetime import datetime, timezone
from flask import render_template, redirect, url_for, flash, request, abort
from app.intake import intake_bp
from app.extensions import limiter
from app.models import IntakeLink, DashboardSession
from app.store import submission_store, Submission
from app.schemas.crime_types import CRIME_SCHEMAS

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
    
    schema = link.form_schema
    crime_types = schema.get("crime_types", list(CRIME_SCHEMAS.keys()))
    crime_labels = {k: CRIME_SCHEMAS.get(k, {}).get("label", k) for k in crime_types}
    questions_by_crime = schema.get("questions_by_crime", {k: CRIME_SCHEMAS[k]["questions"] for k in crime_types if k in CRIME_SCHEMAS})
    
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
    
    schema = link.form_schema
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
    cpf = request.form.get("cpf", "").strip() or None
    address = request.form.get("address", "").strip() or None
    narrative = request.form.get("narrative", "").strip() or None
    
    # collect answers
    questions = CRIME_SCHEMAS.get(crime_type, {}).get("questions", [])
    answers = {}
    for q in questions:
        val = request.form.get(f"q_{q['id']}", "").strip()
        if q["type"] == "boolean":
            answers[q["id"]] = val.lower() in ("1", "true", "yes", "sim", "on")
        else:
            answers[q["id"]] = val if val else None
    
    # process photos
    photos = []
    files = request.files.getlist("photos")
    allowed_mime = {"image/jpeg", "image/png"}
    for f in files[:max_photos]:
        if not f or not f.filename:
            continue
        if f.mimetype not in allowed_mime:
            continue
        data = f.read(max_photo_size + 1)
        if len(data) > max_photo_size:
            continue
        photos.append(_strip_exif(data))
    
    sub = Submission(
        submission_id=str(uuid.uuid4()),
        dashboard_id=session.id,
        guest_name=guest_name,
        dob=dob,
        rg=rg,
        cpf=cpf,
        address=address,
        answers=answers,
        narrative=narrative,
        crime_type=crime_type,
        photos=photos,
        received_at=datetime.now(timezone.utc),
    )

    # Duplicate check — same name or same RG within this dashboard
    if submission_store.is_duplicate(sub):
        flash(
            "Já existe um registro com esse nome ou RG neste plantão. "
            "Se necessário, informe o policial.",
            "warning",
        )
        return redirect(url_for("intake.form", token=token))

    submission_store.add(sub)
    
    return redirect(url_for("intake.ok", token=token))

@intake_bp.route("/t/<token>/ok")
def ok(token):
    return render_template("intake/ok.html")
