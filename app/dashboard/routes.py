# app/dashboard/routes.py

import io
import re
import secrets
from datetime import datetime, timezone
import qrcode
import qrcode.image.svg
from flask import render_template, redirect, url_for, flash, request, abort, Response
from flask_login import login_required, current_user
from app.dashboard import dashboard_bp
from app.extensions import db
from app.models import DashboardSession, IntakeLink, MinimalLogEntry, AccessLog
from app.store import submission_store
from app.schemas.crime_types import DEFAULT_FORM_SCHEMA


def _persist_pending_submissions(session: DashboardSession, *, status: str = "received") -> int:
    """
    Grava em MinimalLogEntry tudo que ainda estiver pendente em RAM para esta triagem.
    Não purge aqui — isso continua sendo responsabilidade do caller.
    """
    pending = submission_store.list_for_dashboard(session.id)
    if not pending:
        return 0

    now = datetime.now(timezone.utc)
    count = 0
    for sub in pending:
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

    return render_template("dashboard/index.html", sessions=sessions, recent_logs=recent_logs)


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
    try:
        duration_hours = int(request.form.get('duration_hours', max_hours))
    except (ValueError, TypeError):
        duration_hours = max_hours

    if duration_hours > max_hours:
        flash(f'Duração excede o limite do seu plano ({max_hours}h).', 'danger')
        return redirect(url_for("dashboard.index"))

    duration_hours = max(1, min(duration_hours, max_hours))

    from datetime import timedelta
    session = DashboardSession(
        user_id=current_user.id,
        label=label,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=duration_hours),
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

    # Track usage
    increment_sessions_created(current_user.id)

    flash(f"Triagem '{label}' criada com sucesso.", "success")
    return redirect(url_for("dashboard.session_detail", session_id=session.id))


@dashboard_bp.route("/sessions/<int:session_id>")
@login_required
def session_detail(session_id):
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

    submissions = submission_store.list_for_dashboard(session.id) if session.is_active else []
    logs = session.logs.order_by(MinimalLogEntry.received_at.desc()).all()

    return render_template(
        "dashboard/session_detail.html",
        session=session,
        link=link,
        qr_svg=qr_svg,
        intake_url=intake_url,
        submissions=submissions,
        logs=logs,
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

    if not session.is_active:
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