# app/dashboard/routes.py

import io
import logging
import re
import secrets
from datetime import datetime, timezone
import qrcode
import qrcode.image.svg
from flask import render_template, redirect, url_for, flash, request, abort, Response, jsonify
from flask_login import login_required, current_user
from app.dashboard import dashboard_bp
from app.extensions import db
from app.models import (
    DashboardSession, IntakeLink, MinimalLogEntry, AccessLog,
    SessionCollaborator, CustomIntakeTemplate,
)
from app.store import submission_store
from app.schemas.crime_types import DEFAULT_FORM_SCHEMA
from app.utils.access_control import can_access_session
from app.utils.plan_helpers import can_share_session, can_join_shared_session, can_create_custom_schema, can_use_infinite_sessions

logger = logging.getLogger(__name__)


def _persist_pending_submissions(session: DashboardSession, *, status: str = "received") -> int:
    """
    Grava em MinimalLogEntry tudo que ainda estiver pendente em RAM para esta triagem.
    Garante idempotência: não duplica se já existir entrada com mesmos dashboard_id,
    guest_display_name e received_at.
    Não purge aqui — isso continua sendo responsabilidade do caller.
    """
    pending = submission_store.list_for_dashboard(session.id)
    if not pending:
        return 0

    def _naive_utc(dt):
        """Return a naive UTC datetime for comparison (strips tzinfo if present)."""
        if dt is None:
            return None
        if getattr(dt, 'tzinfo', None) is not None:
            return dt.replace(tzinfo=None)
        return dt

    # Fetch all existing entries for this session in one query (avoids N+1)
    existing_entries = MinimalLogEntry.query.filter_by(
        dashboard_id=session.id,
    ).with_entities(
        MinimalLogEntry.guest_display_name,
        MinimalLogEntry.received_at,
    ).all()
    existing_keys = {(e.guest_display_name, _naive_utc(e.received_at)) for e in existing_entries}

    now = datetime.now(timezone.utc)
    count = 0
    for sub in pending:
        if (sub.guest_name, _naive_utc(sub.received_at)) in existing_keys:
            continue
        db.session.add(
            MinimalLogEntry(
                dashboard_id=session.id,
                police_user_id=session.user_id,
                guest_display_name=sub.guest_name,
                crime_type=sub.crime_type,
                received_at=sub.received_at,
                closed_at=now,      # momento do encerramento
                status=status,      # mantém "received" para não quebrar UI
            )
        )
        count += 1
    return count



def _expire_stale_sessions_for_user(user_id: int) -> int:
    """
    Expira plantões ativos já vencidos para o usuário informado.
    Persiste pendências em log, apaga dados sensíveis em RAM e inativa links.
    Retorna a quantidade de plantões expirados.
    """
    active_sessions = DashboardSession.query.filter_by(
        user_id=user_id,
        is_active=True,
    ).all()

    expired_count = 0

    for session in active_sessions:
        if not session.is_expired:
            continue

        _persist_pending_submissions(session, status="received")
        submission_store.purge_dashboard(session.id)

        for link in session.links.filter_by(is_active=True).all():
            link.is_active = False

        session.is_active = False
        expired_count += 1

    if expired_count:
        db.session.commit()

    return expired_count


def _expire_session_if_needed(session: DashboardSession) -> bool:
    """
    Expira uma sessão específica caso ela ainda esteja ativa e já tenha vencido.
    Persiste pendências em log, apaga dados sensíveis em RAM e inativa links.
    Retorna True se a sessão foi expirada agora.
    """
    if not session or not session.is_active or not session.is_expired:
        return False

    _persist_pending_submissions(session, status="received")
    submission_store.purge_dashboard(session.id)

    for link in session.links.filter_by(is_active=True).all():
        link.is_active = False

    session.is_active = False
    db.session.commit()
    return True


@dashboard_bp.route("/")
@login_required
def index():
    _expire_stale_sessions_for_user(current_user.id)

    sessions = DashboardSession.query.filter_by(
        user_id=current_user.id
    ).order_by(DashboardSession.created_at.desc()).all()

    # total = pendentes (RAM) + logs (DB)
    for s in sessions:
        pending = submission_store.count_for_dashboard(s.id) if s.is_active else 0
        closed = s.logs.count()
        s.total_records = pending + closed  # atributo dinâmico pro template

    recent_logs = MinimalLogEntry.query.filter_by(
        police_user_id=current_user.id
    ).order_by(MinimalLogEntry.received_at.desc()).limit(20).all()

    return render_template("dashboard/index.html", sessions=sessions, recent_logs=recent_logs,
                           max_duration_hours=current_user.get_current_plan_limits().get('max_session_duration_hours', 12))


@dashboard_bp.route("/sessions/new", methods=["POST"])
@login_required
def new_session():
    label = request.form.get("label", "").strip()
    if not label:
        flash("Informe um nome para a triagem.", "warning")
        return redirect(url_for("dashboard.index"))

    # Plan limit: max sessions per month
    from app.decorators import increment_sessions_created
    from app.models import PlanUsage
    from datetime import datetime, timezone
    limits = current_user.get_current_plan_limits()
    month = datetime.now(timezone.utc).strftime('%Y-%m')
    usage = PlanUsage.query.filter_by(user_id=current_user.id, month=month).first()
    sessions_this_month = usage.sessions_created if usage else 0
    if sessions_this_month >= limits['max_sessions_per_month']:
        flash(
            f"Limite de {limits['max_sessions_per_month']} triagens/mês atingido no seu plano. "
            "Faça upgrade para continuar.",
            'warning',
        )
        return redirect(url_for("dashboard.index"))

    total_count = DashboardSession.query.filter_by(user_id=current_user.id).count()
    if total_count >= 12:
        flash("Você tem 12 triagens no histórico. Delete uma triagem antiga antes de criar nova.", "warning")
        return redirect(url_for("dashboard.index"))

    active_count = DashboardSession.query.filter_by(
        user_id=current_user.id, is_active=True
    ).count()
    if active_count >= 1:
        flash("Você já tem 1 triagem ativa. Feche a triagem atual antes de criar nova.", "warning")
        return redirect(url_for("dashboard.index"))

    # Use duration from form, capped by plan limit
    max_hours = limits.get('max_session_duration_hours', 12)
    from datetime import timedelta
    intake_type = request.form.get("intake_type", "police")
    custom_template_id = None

    if intake_type == "custom":
        if not can_create_custom_schema(current_user):
            flash("Templates personalizados são exclusivos para usuários Enterprise.", "warning")
            return redirect(url_for("dashboard.index"))
        raw_template_id = request.form.get("custom_template_id", "").strip()
        if not raw_template_id:
            flash("Selecione um template personalizado.", "warning")
            return redirect(url_for("dashboard.index"))
        try:
            custom_template_id = int(raw_template_id)
        except (ValueError, TypeError):
            flash("Template inválido.", "warning")
            return redirect(url_for("dashboard.index"))
        template = CustomIntakeTemplate.query.filter_by(
            id=custom_template_id, user_id=current_user.id, is_active=True
        ).first()
        if not template:
            flash("Template não encontrado.", "warning")
            return redirect(url_for("dashboard.index"))
    else:
        intake_type = "police"

    # Handle infinite sessions: only Enterprise + Custom intake
    is_infinite = False
    expires_at = None
    if can_use_infinite_sessions(current_user, intake_type) and request.form.get('is_infinite') == 'true':
        is_infinite = True
        expires_at = None
    else:
        try:
            duration_hours = int(request.form.get('duration_hours', max_hours))
        except (ValueError, TypeError):
            duration_hours = max_hours

        if duration_hours > max_hours:
            flash(f'Duração excede o limite do seu plano ({max_hours}h).', 'danger')
            return redirect(url_for("dashboard.index"))

        duration_hours = max(1, min(duration_hours, max_hours))
        expires_at = datetime.now(timezone.utc) + timedelta(hours=duration_hours)

    session = DashboardSession(
        user_id=current_user.id,
        label=label,
        expires_at=expires_at,
        is_infinite=is_infinite,
        intake_type=intake_type,
        custom_template_id=custom_template_id,
    )
    db.session.add(session)
    db.session.commit()

    # auto-create one intake link
    link = IntakeLink(
        dashboard_id=session.id,
        form_schema=DEFAULT_FORM_SCHEMA,
    )
    db.session.add(link)
    db.session.commit()

    # Auto-generate join_code for Enterprise users
    if can_share_session(current_user):
        for _ in range(10):
            code = secrets.token_hex(3).upper()
            if not DashboardSession.query.filter_by(join_code=code).first():
                session.join_code = code
                db.session.commit()
                break
        else:
            logger.warning(
                "Failed to generate unique join_code for session %s (user %s) after 10 attempts",
                session.id, current_user.id,
            )

    # Track usage
    increment_sessions_created(current_user.id)

    flash(f"Triagem '{label}' criada com sucesso.", "success")
    return redirect(url_for("dashboard.session_detail", session_id=session.id))


@dashboard_bp.route("/sessions/<int:session_id>")
@login_required
def session_detail(session_id):
    session = DashboardSession.query.get_or_404(session_id)

    # Verify access (owner or collaborator)
    can_access, role = can_access_session(current_user, session)
    if not can_access:
        abort(403)

    _expire_session_if_needed(session)

    link = session.links.filter_by(is_active=True).first()
    qr_svg = None
    intake_url = None
    if session.is_active and link:
        intake_url = url_for("intake.form", token=link.token, _external=True, _scheme=request.scheme)
        qr_svg = _generate_qr_svg(intake_url)

    submissions = submission_store.list_for_dashboard(session.id) if session.is_active else []
    logs = session.logs.order_by(MinimalLogEntry.received_at.desc()).all()

    # Build list of links for template compatibility
    links = session.links.all()

    # Determine schema for custom intake rendering
    schema = None
    if session.intake_type == "custom" and session.custom_template:
        schema = session.custom_template.schema

    return render_template(
        "dashboard/session_detail.html",
        session=session,
        role=role,
        link=link,
        links=links,
        qr_svg=qr_svg,
        intake_url=intake_url,
        submissions=submissions,
        logs=logs,
        schema=schema,
        user_can_share=can_share_session(current_user),
        user_can_join=can_join_shared_session(current_user),
    )

@dashboard_bp.route("/sessions/<int:session_id>/close", methods=["POST"])
@login_required
def close_session(session_id):
    session = DashboardSession.query.filter_by(
        id=session_id, user_id=current_user.id
    ).first_or_404()

    _expire_session_if_needed(session)

    if not session.is_active:
        flash("Esta triagem já estava encerrada ou expirada.", "info")
        return redirect(url_for("dashboard.index"))

    # Persistir pendentes antes de apagar RAM
    saved = _persist_pending_submissions(session, status="received")

    session.is_active = False
    submission_store.purge_dashboard(session.id)

    for link in session.links:
        link.is_active = False

    db.session.commit()
    flash(f"Triagem encerrada. {saved} registro(s) pendente(s) foram salvos no histórico.", "info")
    return redirect(url_for("dashboard.index"))

@dashboard_bp.route("/sessions/<int:session_id>/links/new", methods=["POST"])
@login_required
def new_link(session_id):
    session = DashboardSession.query.filter_by(
        id=session_id, user_id=current_user.id
    ).first_or_404()

    _expire_session_if_needed(session)

    if not session.is_active:
        flash("Esta triagem já expirou e não pode receber novos links.", "warning")
        return redirect(url_for("dashboard.session_detail", session_id=session.id))

    link = IntakeLink(
        dashboard_id=session.id,
        form_schema=DEFAULT_FORM_SCHEMA,
    )
    db.session.add(link)
    db.session.commit()

    flash("Novo link criado.", "success")
    return redirect(url_for("dashboard.session_detail", session_id=session.id))

@dashboard_bp.route("/sessions/<int:session_id>/purge", methods=["POST"])
@login_required
def purge_session(session_id):
    session = DashboardSession.query.filter_by(
        id=session_id, user_id=current_user.id
    ).first_or_404()
    submission_store.purge_dashboard(session.id)
    flash("Dados sensíveis apagados.", "info")
    return redirect(url_for("dashboard.session_detail", session_id=session.id))


@dashboard_bp.route("/sessions/delete-closed", methods=["POST"])
@login_required
def delete_closed_sessions():
    closed = DashboardSession.query.filter_by(
        user_id=current_user.id, is_active=False
    ).all()
    for s in closed:
        MinimalLogEntry.query.filter_by(dashboard_id=s.id).delete()
        IntakeLink.query.filter_by(dashboard_id=s.id).delete()
        db.session.delete(s)
    db.session.commit()
    flash(f"{len(closed)} triagem(ns) encerrada(s) apagada(s).", "info")
    return redirect(url_for("dashboard.index"))


@dashboard_bp.route("/sessions/<int:session_id>/delete", methods=["POST"])
@login_required
def delete_session(session_id):
    session = DashboardSession.query.filter_by(
        id=session_id, user_id=current_user.id
    ).first_or_404()

    if session.is_active:
        flash("Feche a triagem antes de deletar.", "warning")
        return redirect(url_for("dashboard.session_detail", session_id=session.id))

    MinimalLogEntry.query.filter_by(dashboard_id=session.id).delete()
    IntakeLink.query.filter_by(dashboard_id=session.id).delete()
    db.session.delete(session)
    db.session.commit()

    flash("Triagem deletada com sucesso.", "info")
    return redirect(url_for("dashboard.index"))


@dashboard_bp.route("/sessions/<int:session_id>/print-qr")
@login_required
def print_qr(session_id):
    session = DashboardSession.query.filter_by(
        id=session_id, user_id=current_user.id
    ).first_or_404()

    _expire_session_if_needed(session)

    link = session.links.filter_by(is_active=True).first()
    qr_svg = None
    intake_url = None
    if session.is_active and link:
        intake_url = url_for("intake.form", token=link.token, _external=True, _scheme=request.scheme)
        qr_svg = _generate_qr_svg(intake_url)

    return render_template(
        "dashboard/print_qr.html",
        session=session,
        qr_svg=qr_svg,
        intake_url=intake_url,
    )


@dashboard_bp.route("/my-audit-log")
@login_required
def my_audit_log():
    """Display the current officer's access audit log (last 100 entries)."""
    logs = (
        AccessLog.query.filter_by(user_id=current_user.id)
        .order_by(AccessLog.accessed_at.desc())
        .limit(100)
        .all()
    )
    return render_template("dashboard/audit_log.html", logs=logs)


@dashboard_bp.route("/sessions/join", methods=["GET", "POST"])
@login_required
def join_session():
    """Permite usuário Premium/Enterprise entrar em sessão via join_code."""
    if request.method == "POST":
        code = request.form.get("join_code", "").strip().upper()

        # Validar plano (FREE não pode)
        if not can_join_shared_session(current_user):
            flash(
                "Usuários do plano Free não podem participar de triagens compartilhadas. "
                "Faça upgrade para Premium ou Enterprise.",
                "warning"
            )
            return redirect(url_for("plans.index"))

        # Buscar sessão por join_code
        session = DashboardSession.query.filter_by(join_code=code).first()

        if not session:
            flash("Código inválido.", "danger")
            return redirect(url_for("dashboard.index"))

        if not session.is_active or session.is_expired:
            flash("Esta triagem já foi encerrada ou expirou.", "warning")
            return redirect(url_for("dashboard.index"))

        # Não pode entrar na própria sessão
        if session.user_id == current_user.id:
            flash("Você já é o criador desta triagem.", "info")
            return redirect(url_for("dashboard.session_detail", session_id=session.id))

        # Verificar se já é colaborador
        existing = SessionCollaborator.query.filter_by(
            session_id=session.id,
            user_id=current_user.id
        ).first()

        if existing:
            flash("Você já está participando desta triagem.", "info")
            return redirect(url_for("dashboard.session_detail", session_id=session.id))

        # Criar colaborador
        collab = SessionCollaborator(
            session_id=session.id,
            user_id=current_user.id
        )
        db.session.add(collab)
        db.session.commit()

        flash(f"Você entrou na triagem '{session.label}' como convidado.", "success")
        return redirect(url_for("dashboard.session_detail", session_id=session.id))

    return render_template("dashboard/join_session.html")


@dashboard_bp.route("/sessions/<int:session_id>/generate-code", methods=["POST"])
@login_required
def generate_join_code(session_id):
    """Gera (ou regenera) join_code único de 6 caracteres. OWNER ONLY. Enterprise apenas."""
    session = DashboardSession.query.get_or_404(session_id)

    if session.user_id != current_user.id:
        abort(403)

    if not can_share_session(current_user):
        return jsonify({"error": "Apenas usuários Enterprise podem compartilhar triagens"}), 403

    max_attempts = 10
    for _ in range(max_attempts):
        code = secrets.token_hex(3).upper()
        if not DashboardSession.query.filter_by(join_code=code).first():
            session.join_code = code
            db.session.commit()
            return jsonify({"join_code": code})

    return jsonify({"error": "Falha ao gerar código único"}), 500


@dashboard_bp.route("/sessions/<int:session_id>/collaborators")
@login_required
def list_collaborators(session_id):
    """Lista todos os colaboradores de uma sessão. OWNER ONLY."""
    session = DashboardSession.query.get_or_404(session_id)

    if session.user_id != current_user.id:
        abort(403)

    collabs = SessionCollaborator.query.filter_by(session_id=session_id).all()

    return jsonify([{
        "user_id": c.user_id,
        "display_name": c.user.display_name,
        "joined_at": c.joined_at.isoformat()
    } for c in collabs])


@dashboard_bp.route("/sessions/<int:session_id>/collaborators/<int:user_id>", methods=["DELETE"])
@login_required
def remove_collaborator(session_id, user_id):
    """Remove um colaborador da sessão. OWNER ONLY."""
    session = DashboardSession.query.get_or_404(session_id)

    if session.user_id != current_user.id:
        abort(403)

    deleted = SessionCollaborator.query.filter_by(
        session_id=session_id,
        user_id=user_id
    ).delete()

    db.session.commit()

    if deleted:
        return jsonify({"status": "removed"})
    return jsonify({"error": "Colaborador não encontrado"}), 404


@dashboard_bp.route("/custom-templates")
@login_required
def list_custom_templates():
    if not can_create_custom_schema(current_user):
        flash("Modelos personalizados são exclusivos para usuários Enterprise.", "warning")
        return redirect(url_for("dashboard.index"))
    templates = CustomIntakeTemplate.query.filter_by(
        user_id=current_user.id, is_active=True
    ).order_by(CustomIntakeTemplate.created_at.desc()).all()
    return render_template("dashboard/custom_templates_list.html", templates=templates)


@dashboard_bp.route("/custom-templates/create", methods=["GET", "POST"])
@login_required
def create_custom_template():
    from app.decorators import can_create_custom_template
    from app.utils.schema_validator import validate_custom_intake_schema
    import json

    allowed, error = can_create_custom_template(current_user)
    if not allowed:
        flash(error, "warning")
        return redirect(url_for("dashboard.list_custom_templates"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not name:
            flash("Informe um nome para o template.", "warning")
            return render_template("dashboard/custom_template_create.html")

        schema_json = request.form.get("schema_json", "").strip()
        try:
            schema = json.loads(schema_json)
        except (ValueError, TypeError):
            flash("Schema inválido (JSON malformado).", "danger")
            return render_template("dashboard/custom_template_create.html")

        valid, err = validate_custom_intake_schema(schema)
        if not valid:
            flash(f"Schema inválido: {err}", "danger")
            return render_template("dashboard/custom_template_create.html")

        # Add allow_attachments flag to schema
        allow_attachments = request.form.get("allow_attachments") == "true"
        schema['allow_attachments'] = allow_attachments

        template = CustomIntakeTemplate(
            user_id=current_user.id,
            name=name,
            schema=schema,
        )
        db.session.add(template)
        db.session.commit()

        flash(f"Template '{name}' criado com sucesso.", "success")
        return redirect(url_for("dashboard.list_custom_templates"))

    return render_template("dashboard/custom_template_create.html")


@dashboard_bp.route("/custom-templates/<int:template_id>/delete", methods=["POST"])
@login_required
def delete_custom_template(template_id):
    template = CustomIntakeTemplate.query.filter_by(
        id=template_id, user_id=current_user.id
    ).first_or_404()
    template.is_active = False
    db.session.commit()
    flash("Template removido.", "info")
    return redirect(url_for("dashboard.list_custom_templates"))


@dashboard_bp.route("/custom-templates/<int:template_id>/edit", methods=["GET", "POST"])
@login_required
def edit_custom_template(template_id):
    """Editar modelo personalizado existente."""
    from app.utils.schema_validator import validate_custom_intake_schema
    import json

    if not can_create_custom_schema(current_user):
        flash("Modelos personalizados são exclusivos para usuários Enterprise.", "warning")
        return redirect(url_for("dashboard.index"))

    template = CustomIntakeTemplate.query.filter_by(
        id=template_id, user_id=current_user.id, is_active=True
    ).first_or_404()

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not name:
            flash("Informe um nome para o template.", "warning")
            return render_template("dashboard/custom_template_edit.html", template=template)

        schema_json = request.form.get("schema_json", "").strip()
        try:
            schema = json.loads(schema_json)
        except (ValueError, TypeError):
            flash("Schema inválido (JSON malformado).", "danger")
            return render_template("dashboard/custom_template_edit.html", template=template)

        valid, err = validate_custom_intake_schema(schema)
        if not valid:
            flash(f"Schema inválido: {err}", "danger")
            return render_template("dashboard/custom_template_edit.html", template=template)

        allow_attachments = request.form.get("allow_attachments") == "true"
        schema['allow_attachments'] = allow_attachments

        template.name = name
        template.schema = schema
        db.session.commit()

        flash(f"Template '{name}' atualizado com sucesso.", "success")
        return redirect(url_for("dashboard.list_custom_templates"))

    return render_template("dashboard/custom_template_edit.html", template=template)


@dashboard_bp.route("/sessions/<int:session_id>/submissions/<submission_id>/csv")
@login_required
def export_submission_csv(session_id, submission_id):
    """Exportar submission individual como CSV."""
    from app.utils.csv_helpers import generate_csv_response

    session = DashboardSession.query.get_or_404(session_id)

    can_access, _role = can_access_session(current_user, session)
    if not can_access:
        abort(403)

    sub = None
    if session.is_active:
        sub = submission_store.get(submission_id)

    if sub and sub.dashboard_id == session_id:
        rows = [
            ['Campo', 'Valor'],
            ['Nome', sub.guest_name],
            ['Data Nascimento', sub.dob or ''],
            ['RG', sub.rg or ''],
            ['CPF', sub.cpf or ''],
            ['Telefone', sub.phone or ''],
            ['Endereço', sub.address or ''],
            ['Tipo', sub.crime_type],
            ['Narrativa', sub.narrative or ''],
            ['Recebido em', sub.received_at.isoformat() if sub.received_at else ''],
        ]
        for key, value in (sub.answers or {}).items():
            rows.append([f'Resposta: {key}', str(value)])
        return generate_csv_response(rows, f"submission_{submission_id}.csv")

    try:
        log_id = int(submission_id)
    except (ValueError, TypeError):
        abort(404)

    log = MinimalLogEntry.query.filter_by(
        dashboard_id=session_id,
        id=log_id,
    ).first_or_404()

    rows = [
        ['Campo', 'Valor'],
        ['Nome', log.guest_display_name or ''],
        ['Tipo', log.crime_type or ''],
        ['Recebido em', log.received_at.isoformat() if log.received_at else ''],
        ['Encerrado em', log.closed_at.isoformat() if log.closed_at else ''],
        ['Status', log.status or ''],
    ]
    return generate_csv_response(rows, f"submission_{submission_id}.csv")


@dashboard_bp.route("/sessions/<int:session_id>/export-all-csv")
@login_required
def export_session_csv(session_id):
    """Exportar todas as submissions da sessão como CSV."""
    from app.utils.csv_helpers import generate_csv_response

    session = DashboardSession.query.get_or_404(session_id)

    can_access, _role = can_access_session(current_user, session)
    if not can_access:
        abort(403)

    rows = [
        ['ID', 'Nome', 'Tipo', 'Data Nascimento', 'RG', 'CPF',
         'Telefone', 'Narrativa', 'Recebido em', 'Status'],
    ]

    if session.is_active:
        for sub in submission_store.list_for_dashboard(session.id):
            rows.append([
                sub.submission_id,
                sub.guest_name,
                sub.crime_type,
                sub.dob or '',
                sub.rg or '',
                sub.cpf or '',
                sub.phone or '',
                sub.narrative or '',
                sub.received_at.isoformat() if sub.received_at else '',
                'ativo',
            ])

    for log in session.logs.order_by(MinimalLogEntry.received_at.desc()).all():
        rows.append([
            log.id,
            log.guest_display_name or '',
            log.crime_type or '',
            '', '', '', '', '',
            log.received_at.isoformat() if log.received_at else '',
            log.status or '',
        ])

    safe_label = re.sub(r'[^\w\-]', '_', session.label)
    filename = f"sessao_{session.id}_{safe_label}.csv"
    return generate_csv_response(rows, filename)


def _generate_qr_svg(url: str) -> str:
    """Generate a clean inline SVG QR code string."""
    try:
        factory = qrcode.image.svg.SvgPathImage
        qr = qrcode.QRCode(version=1, box_size=8, border=2)
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(image_factory=factory)
        buf = io.BytesIO()
        img.save(buf)
        svg_str = buf.getvalue().decode("utf-8")
        svg_str = re.sub(r'<\?xml[^?]*\?>\s*', '', svg_str)
        svg_str = re.sub(r'<!DOCTYPE[^>]*>\s*', '', svg_str)
        return svg_str.strip()
    except Exception:
        return ""