"""Celery tasks for cleanup operations."""

import logging
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)


try:
    from app.celery_app import celery_app

    @celery_app.task(name="app.tasks.cleanup.cleanup_orphan_photos")
    def cleanup_orphan_photos():
        """Delete orphaned photos from S3 (photos without active submissions)."""
        from app import create_app
        from config import Config
        from app.redis_client import get_redis_client

        app = create_app(Config)
        with app.app_context():
            # Distributed lock to avoid concurrent execution
            redis_client = get_redis_client()
            lock_key = "lock:cleanup_orphan_photos"
            if redis_client:
                if not redis_client.set(lock_key, "1", nx=True, ex=3500):
                    logger.info("Another worker is already running cleanup_orphan_photos")
                    return

            try:
                storage = getattr(app, "photo_storage", None)
                if not storage or not hasattr(storage, "list_all"):
                    logger.info("S3 storage not configured or doesn't support list_all")
                    return

                from app.store import submission_store
                from app.models import DashboardSession

                # Collect all active photo keys
                active_keys = set()
                active_sessions = DashboardSession.query.filter_by(is_active=True).all()
                for session in active_sessions:
                    subs = submission_store.list_for_dashboard(session.id)
                    for sub in subs:
                        if sub.photo_keys:
                            active_keys.update(sub.photo_keys)

                # Scan S3 and delete orphans
                deleted = 0
                try:
                    all_keys = storage.list_all()
                    for key in all_keys:
                        if key not in active_keys:
                            if storage.delete(key):
                                deleted += 1
                except Exception as exc:
                    logger.error("Error cleaning orphan photos: %s", exc)

                logger.info("Cleaned %d orphan photos from S3", deleted)
            finally:
                if redis_client:
                    redis_client.delete(lock_key)

    @celery_app.task(name="app.tasks.cleanup.cleanup_old_access_logs")
    def cleanup_old_access_logs():
        """Delete access logs older than 30 days."""
        from app import create_app
        from config import Config
        from app.extensions import db
        from app.models import AccessLog
        from app.redis_client import get_redis_client

        app = create_app(Config)
        with app.app_context():
            # Distributed lock to avoid concurrent execution
            redis_client = get_redis_client()
            lock_key = "lock:cleanup_old_access_logs"
            if redis_client:
                if not redis_client.set(lock_key, "1", nx=True, ex=3500):
                    logger.info("Another worker is already running cleanup_old_access_logs")
                    return

            try:
                cutoff = datetime.now(timezone.utc) - timedelta(days=30)
                count = AccessLog.query.filter(AccessLog.accessed_at < cutoff).delete()
                db.session.commit()
                logger.info("Deleted %d old access log entries", count)
            finally:
                if redis_client:
                    redis_client.delete(lock_key)

    @celery_app.task(name="app.tasks.cleanup.cleanup_old_minimal_logs")
    def cleanup_old_minimal_logs():
        """Delete minimal log entries older than 180 days."""
        from app import create_app
        from config import Config
        from app.extensions import db
        from app.models import MinimalLogEntry
        from app.redis_client import get_redis_client

        app = create_app(Config)
        with app.app_context():
            # Distributed lock
            redis_client = get_redis_client()
            lock_key = "lock:cleanup_old_minimal_logs"
            if redis_client:
                if not redis_client.set(lock_key, "1", nx=True, ex=3500):
                    logger.info("Another worker is already running cleanup_old_minimal_logs")
                    return

            try:
                cutoff = datetime.now(timezone.utc) - timedelta(days=180)
                count = MinimalLogEntry.query.filter(
                    MinimalLogEntry.received_at < cutoff
                ).delete()
                db.session.commit()
                logger.info("Deleted %d old minimal log entries (older than 180 days)", count)
            finally:
                if redis_client:
                    redis_client.delete(lock_key)

except Exception:
    # Celery not configured — tasks will not be registered.
    pass
