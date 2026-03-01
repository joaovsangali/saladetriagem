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
from app.models import DashboardSession, IntakeLink, MinimalLogEntry
from app.store import submission_store
from app.schemas.crime_types import DEFAULT_FORM_SCHEMA

@dashboard_bp.route("/")
@login_required
def index():
    sessions = DashboardSession.query.filter_by(
        user_id=current_user.id
    ).order_by(DashboardSession.created_at.desc()).all()
    
    recent_logs = MinimalLogEntry.query.filter_by(
        police_user_id=current_user.id
    ).order_by(MinimalLogEntry.received_at.desc()).limit(20).all()
    
    pending_counts = {s.id: submission_store.count_for_dashboard(s.id) for s in sessions}
    
    return render_template("dashboard/index.html", sessions=sessions, recent_logs=recent_logs, pending_counts=pending_counts)

@dashboard_bp.route("/sessions/new", methods=["POST"])
@login_required
def new_session():
    label = request.form.get("label", "").strip()
    if not label:
        flash("Informe um nome para o plantão.", "warning")
        return redirect(url_for("dashboard.index"))
    
    active_count = DashboardSession.query.filter_by(
        user_id=current_user.id, is_active=True
    ).count()
    if active_count >= current_user.max_dashboards:
        flash(f"Limite de {current_user.max_dashboards} dashboards ativos atingido.", "warning")
        return redirect(url_for("dashboard.index"))
    
    session = DashboardSession(
        user_id=current_user.id,
        label=label,
        expires_at=DashboardSession.make_expires_at(),
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
    
    flash(f"Plantão '{label}' criado com sucesso.", "success")
    return redirect(url_for("dashboard.session_detail", session_id=session.id))

@dashboard_bp.route("/sessions/<int:session_id>")
@login_required
def session_detail(session_id):
    session = DashboardSession.query.filter_by(
        id=session_id, user_id=current_user.id
    ).first_or_404()
    
    link = session.links.filter_by(is_active=True).first()
    qr_svg = None
    intake_url = None
    if link:
        intake_url = url_for("intake.form", token=link.token, _external=True)
        qr_svg = _generate_qr_svg(intake_url)
    
    submissions = submission_store.list_for_dashboard(session.id)
    logs = session.logs.order_by(MinimalLogEntry.received_at.desc()).all()
    
    # Statistics: crime type breakdown
    from collections import Counter
    from app.schemas.crime_types import CRIME_SCHEMAS
    crime_labels = {k: v["label"] for k, v in CRIME_SCHEMAS.items()}
    stats_pending = Counter(s.crime_type for s in submissions)
    stats_closed = Counter(log.crime_type for log in logs if log.status == "closed")
    stats_discarded = Counter(log.crime_type for log in logs if log.status == "discarded")
    
    return render_template(
        "dashboard/session_detail.html",
        session=session,
        link=link,
        qr_svg=qr_svg,
        intake_url=intake_url,
        submissions=submissions,
        logs=logs,
        crime_labels=crime_labels,
        stats_pending=stats_pending,
        stats_closed=stats_closed,
        stats_discarded=stats_discarded,
    )

@dashboard_bp.route("/sessions/<int:session_id>/close", methods=["POST"])
@login_required
def close_session(session_id):
    session = DashboardSession.query.filter_by(
        id=session_id, user_id=current_user.id
    ).first_or_404()
    session.is_active = False
    submission_store.purge_dashboard(session.id)
    for link in session.links:
        link.is_active = False
    db.session.commit()
    flash("Plantão encerrado e dados apagados.", "info")
    return redirect(url_for("dashboard.index"))

@dashboard_bp.route("/sessions/<int:session_id>/links/new", methods=["POST"])
@login_required
def new_link(session_id):
    session = DashboardSession.query.filter_by(
        id=session_id, user_id=current_user.id, is_active=True
    ).first_or_404()
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

@dashboard_bp.route("/account", methods=["GET", "POST"])
@login_required
def account():
    if request.method == "POST":
        action = request.form.get("action")
        if action == "update_profile":
            display_name = request.form.get("display_name", "").strip()
            phone = request.form.get("phone", "").strip() or None
            if not display_name:
                flash("Nome não pode ser vazio.", "danger")
            else:
                current_user.display_name = display_name
                current_user.phone = phone
                db.session.commit()
                flash("Perfil atualizado com sucesso.", "success")
        elif action == "change_password":
            current_pwd = request.form.get("current_password", "")
            new_pwd = request.form.get("new_password", "")
            confirm_pwd = request.form.get("confirm_new_password", "")
            if not current_user.check_password(current_pwd):
                flash("Senha atual incorreta.", "danger")
            elif len(new_pwd) < 8:
                flash("A nova senha deve ter no mínimo 8 caracteres.", "danger")
            elif new_pwd != confirm_pwd:
                flash("As novas senhas não coincidem.", "danger")
            else:
                current_user.set_password(new_pwd)
                db.session.commit()
                flash("Senha alterada com sucesso.", "success")
        return redirect(url_for("dashboard.account"))
    return render_template("dashboard/account.html")


@dashboard_bp.route("/sessions/<int:session_id>/extend", methods=["POST"])
@login_required
def extend_session(session_id):
    session = DashboardSession.query.filter_by(
        id=session_id, user_id=current_user.id, is_active=True
    ).first_or_404()
    session.expires_at = DashboardSession.make_expires_at()
    db.session.commit()
    flash("Plantão estendido por mais 24 horas.", "success")
    return redirect(url_for("dashboard.session_detail", session_id=session.id))


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
