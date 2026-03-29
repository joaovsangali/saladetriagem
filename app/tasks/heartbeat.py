"""Celery heartbeat tasks for health monitoring."""

import logging
import time

logger = logging.getLogger(__name__)

try:
    from app.celery_app import celery_app

    @celery_app.task(name="app.tasks.heartbeat.celery_pipeline_heartbeat")
    def celery_pipeline_heartbeat():
        """Heartbeat task executed by Celery worker and scheduled by Celery Beat."""
        from app.redis_client import get_redis_client

        redis_client = get_redis_client()
        if not redis_client:
            logger.warning("Redis unavailable — Celery heartbeat not recorded")
            return False

        now = str(time.time())
        try:
            pipe = redis_client.pipeline()
            pipe.set("celery:pipeline:heartbeat", now, ex=300)
            pipe.set("celery:worker:heartbeat", now, ex=300)
            pipe.execute()
            logger.debug("Celery worker heartbeat updated")
            return True
        except Exception as exc:
            logger.warning("Failed to update Celery heartbeat: %s", exc)
            return False

except Exception:
    # Celery not configured — tasks will not be registered.
    pass