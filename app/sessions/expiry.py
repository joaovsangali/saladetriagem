import threading
import time
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

def start_expiry_daemon(app):
    def _run():
        while True:
            time.sleep(300)  # every 5 minutes
            try:
                _expire_sessions(app)
            except Exception as e:
                logger.exception("Error in expiry daemon: %s", e)
    
    t = threading.Thread(target=_run, daemon=True, name="session-expiry-daemon")
    t.start()
    logger.info("Session expiry daemon started.")

def _expire_sessions(app):
    from app.extensions import db
    from app.models import DashboardSession
    from app.store import submission_store
    
    with app.app_context():
        now = datetime.now(timezone.utc)
        active_sessions = DashboardSession.query.filter_by(is_active=True).all()
        for session in active_sessions:
            expires = session.expires_at
            if expires.tzinfo is None:
                expires = expires.replace(tzinfo=timezone.utc)
            if now >= expires:
                session.is_active = False
                submission_store.purge_dashboard(session.id)
                logger.info("Expired dashboard session %s", session.id)
        db.session.commit()
        
        # Purge orphan submissions (inactive dashboards still in store)
        inactive_sessions = DashboardSession.query.filter_by(is_active=False).all()
        for session in inactive_sessions:
            submission_store.purge_dashboard(session.id)
