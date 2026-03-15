"""Celery task: expire dashboard sessions.

This task replaces (or supplements) the threading daemon in
``app/sessions/expiry.py`` when Celery is available.
"""

import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


def _get_celery_app():
    from app.celery_app import celery_app
    return celery_app


def expire_sessions_task():
    """Core expiry logic shared by both Celery task and threading fallback."""
    from app.extensions import db
    from app.models import DashboardSession, MinimalLogEntry
    from app.store import submission_store

    now = datetime.now(timezone.utc)
    active_sessions = DashboardSession.query.filter_by(is_active=True).all()

    for session in active_sessions:
        expires = session.expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)

        if now >= expires:
            pending = submission_store.list_for_dashboard(session.id)
            if pending:
                now2 = datetime.now(timezone.utc)
                for sub in pending:
                    db.session.add(
                        MinimalLogEntry(
                            dashboard_id=session.id,
                            police_user_id=session.user_id,
                            guest_display_name=sub.guest_name,
                            crime_type=sub.crime_type,
                            received_at=sub.received_at,
                            closed_at=now2,
                            status="received",
                        )
                    )

            session.is_active = False
            submission_store.purge_dashboard(session.id)
            logger.info("Expired dashboard session %s", session.id)

    db.session.commit()

    inactive_sessions = DashboardSession.query.filter_by(is_active=False).all()
    for session in inactive_sessions:
        submission_store.purge_dashboard(session.id)


try:
    from app.celery_app import celery_app

    @celery_app.task(name="app.tasks.session_expiry.expire_sessions")
    def expire_sessions():
        """Celery task to expire stale dashboard sessions."""
        import os
        from app import create_app
        from config import Config

        app = create_app(Config)
        with app.app_context():
            expire_sessions_task()

except Exception:
    # Celery not configured — this module is still importable but the task
    # will not be registered. The threading daemon in expiry.py takes over.
    pass
