"""Plan limit enforcement decorators."""

from functools import wraps

from flask import flash, redirect, url_for
from flask_login import current_user

from app.extensions import db


def require_plan_limit(limit_key: str):
    """Decorator to enforce plan limits before executing a view."""

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            limits = current_user.get_current_plan_limits()

            if limit_key == 'max_sessions_per_month':
                from app.models import PlanUsage, DashboardSession
                from datetime import datetime, timezone
                month = datetime.now(timezone.utc).strftime('%Y-%m')
                usage = PlanUsage.query.filter_by(
                    user_id=current_user.id, month=month
                ).first()
                sessions_this_month = usage.sessions_created if usage else 0
                max_sessions = limits.get('max_sessions_per_month')
                if max_sessions is not None and sessions_this_month >= max_sessions:
                    flash(
                        f"Limite de {max_sessions} plantões/mês atingido. "
                        "Faça upgrade para continuar.",
                        'warning',
                    )
                    return redirect(url_for('account.index'))

            elif limit_key == 'max_submissions_per_session':
                # Get session_id from kwargs
                session_id = kwargs.get('session_id') or kwargs.get('dashboard_id')
                if session_id:
                    from app.store import submission_store
                    count = submission_store.count_for_dashboard(session_id)
                    max_submissions = limits.get('max_submissions_per_session')
                    if max_submissions is not None and count >= max_submissions:
                        flash(
                            f"Limite de {max_submissions} submissões por triagem atingido.",
                            'warning',
                        )
                        return redirect(url_for('dashboard.index'))

            elif limit_key == 'can_view_photos':
                if not limits.get('can_view_photos'):
                    from flask import abort
                    abort(403)

            return f(*args, **kwargs)

        return decorated_function

    return decorator


def _get_or_create_plan_usage(user_id: int, month: str):
    """Get or create a PlanUsage record for the given user and month."""
    from app.models import PlanUsage
    usage = PlanUsage.query.filter_by(user_id=user_id, month=month).first()
    if not usage:
        usage = PlanUsage(user_id=user_id, month=month)
        db.session.add(usage)
        db.session.flush()
    return usage


def increment_sessions_created(user_id: int):
    """Increment the sessions_created counter for the current month."""
    from datetime import datetime, timezone
    month = datetime.now(timezone.utc).strftime('%Y-%m')
    usage = _get_or_create_plan_usage(user_id, month)
    usage.sessions_created += 1
    db.session.commit()


def increment_submissions(user_id: int):
    """Increment total_submissions counter for the current month."""
    from datetime import datetime, timezone
    month = datetime.now(timezone.utc).strftime('%Y-%m')
    usage = _get_or_create_plan_usage(user_id, month)
    usage.total_submissions += 1
    db.session.commit()


def can_create_custom_template(user):
    """Check if user can create a custom template.

    Returns (allowed: bool, error_message: str | None).
    """
    from app.utils.plan_helpers import can_create_custom_schema
    if not can_create_custom_schema(user):
        return False, "Recurso disponível apenas para usuários Enterprise"

    from app.models import CustomIntakeTemplate
    count = CustomIntakeTemplate.query.filter_by(
        user_id=user.id, is_active=True
    ).count()

    if count >= 5:
        return False, "Limite de 5 templates personalizados atingido"

    return True, None
