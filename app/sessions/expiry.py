# app/sessions/expiry.py

import threading
import time
import logging
import warnings
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


def start_expiry_daemon(app):
    """Start a background thread for session expiry.

    .. deprecated::
        Use the Celery Beat task ``app.tasks.session_expiry.expire_sessions``
        instead.  This threading daemon creates one background thread per
        Gunicorn worker, causing race conditions in multi-worker deployments.
        It is kept here only to ease the transition and for local development
        without Celery.
    """
    warnings.warn(
        "start_expiry_daemon() is deprecated. "
        "Configure Celery Beat with the 'expire-sessions-every-5-minutes' "
        "schedule instead.",
        DeprecationWarning,
        stacklevel=2,
    )

    def _run():
        while True:
            time.sleep(300)  # every 5 minutes
            try:
                _expire_sessions(app)
            except Exception as e:
                logger.exception("Error in expiry daemon: %s", e)

    t = threading.Thread(target=_run, daemon=True, name="session-expiry-daemon")
    t.start()
    logger.info("Session expiry daemon started (deprecated — use Celery Beat).")


def _expire_sessions(app):
    from app.extensions import db
    from app.models import DashboardSession, MinimalLogEntry
    from app.store import submission_store

    with app.app_context():
        now = datetime.now(timezone.utc)
        active_sessions = DashboardSession.query.filter_by(is_active=True).all()

        for session in active_sessions:
            expires = session.expires_at
            if expires.tzinfo is None:
                expires = expires.replace(tzinfo=timezone.utc)

            if now >= expires:
                # Persistir pendentes antes de limpar RAM
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

        # Purge orphan submissions (inactive dashboards still in store)
        inactive_sessions = DashboardSession.query.filter_by(is_active=False).all()
        for session in inactive_sessions:
            submission_store.purge_dashboard(session.id)