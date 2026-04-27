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
    from app.models import DashboardSession, MinimalLogEntry, SessionCollaborator
    from app.store import submission_store

    now = datetime.now(timezone.utc)
    active_sessions = DashboardSession.query.filter_by(is_active=True).all()

    for session in active_sessions:
        if session.is_infinite:
            continue  # skip infinite sessions — they never expire automatically

        expires = session.expires_at
        if expires is None:
            continue  # safeguard: no expiry set
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)

        if now >= expires:
            pending = submission_store.list_for_dashboard(session.id)
            if pending:
                now2 = datetime.now(timezone.utc)

                def _naive_utc(dt):
                    if dt is None:
                        return None
                    if getattr(dt, 'tzinfo', None) is not None:
                        return dt.replace(tzinfo=None)
                    return dt

                # Fetch existing entries in one query to avoid N+1
                existing_entries = db.session.query(
                    MinimalLogEntry.guest_display_name,
                    MinimalLogEntry.received_at,
                ).filter_by(dashboard_id=session.id).all()
                existing_keys = {
                    (e.guest_display_name, _naive_utc(e.received_at))
                    for e in existing_entries
                }
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
                            closed_at=now2,
                            status="received",
                        )
                    )

            # Clean up collaborators before marking inactive
            SessionCollaborator.query.filter_by(session_id=session.id).delete()

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
        from app.redis_client import get_redis_client

        app = create_app(Config)
        with app.app_context():
            # Distributed lock to avoid concurrent execution across workers
            redis_client = get_redis_client()
            lock_key = "lock:expire_sessions"

            if redis_client:
                # Acquire lock for 4 minutes (task runs every 5 min)
                if not redis_client.set(lock_key, "1", nx=True, ex=240):
                    logger.info("Another worker is already running expire_sessions")
                    return

            try:
                expire_sessions_task()
            finally:
                if redis_client:
                    redis_client.delete(lock_key)

except Exception:
    # Celery not configured — this module is still importable but the task
    # will not be registered. The threading daemon in expiry.py takes over.
    pass
