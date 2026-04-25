"""Account management routes."""

from datetime import datetime, timezone

from flask import render_template, redirect, url_for, flash, request, session
from flask_login import login_required, current_user

from app.account import account_bp
from app.account.forms import ChangePasswordForm
from app.extensions import db
from app.models import UserSession, PlanUsage
from app.plans import PLANS


@account_bp.route("/")
@login_required
def index():
    limits = current_user.get_current_plan_limits()
    trial_info = current_user.get_trial_info()

    # Monthly usage counter
    month = datetime.now(timezone.utc).strftime('%Y-%m')
    usage = PlanUsage.query.filter_by(user_id=current_user.id, month=month).first()
    sessions_used = usage.sessions_created if usage else 0
    sessions_remaining = max(limits['max_sessions_per_month'] - sessions_used, 0)

    # Active sessions for this user
    active_sessions = (
        UserSession.query.filter_by(user_id=current_user.id, is_active=True)
        .order_by(UserSession.last_activity_at.desc())
        .all()
    )
    current_token = session.get('user_session_token')

    return render_template(
        "account/index.html",
        limits=limits,
        trial_info=trial_info,
        plans=PLANS,
        active_sessions=active_sessions,
        current_token=current_token,
        sessions_used=sessions_used,
        sessions_remaining=sessions_remaining,
    )


@account_bp.route("/change-password", methods=["POST"])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if not current_user.check_password(form.current_password.data):
            flash("Senha atual incorreta.", "danger")
            return redirect(url_for("account.index"))
        current_user.set_password(form.new_password.data)
        db.session.commit()
        flash("Senha alterada com sucesso.", "success")
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(error, "danger")
    return redirect(url_for("account.index"))


@account_bp.route("/end-session/<token>", methods=["POST"])
@login_required
def end_session(token):
    user_session = UserSession.query.filter_by(
        session_token=token,
        user_id=current_user.id,
    ).first_or_404()
    user_session.is_active = False
    db.session.commit()
    flash("Sessão encerrada.", "info")
    return redirect(url_for("account.index"))


@account_bp.route("/end-all-other-sessions", methods=["POST"])
@login_required
def end_all_other_sessions():
    current_token = session.get('user_session_token')
    query = UserSession.query.filter_by(user_id=current_user.id, is_active=True)
    if current_token:
        query = query.filter(UserSession.session_token != current_token)
    count = query.count()
    query.update({'is_active': False}, synchronize_session=False)
    db.session.commit()
    flash(f"{count} sessão(ões) encerrada(s).", "info")
    return redirect(url_for("account.index"))
