"""Celery heartbeat tasks for health monitoring.

Workers and Beat write periodic timestamps to Redis so that the /health
endpoint can verify they are alive without requiring Celery inspect API.
"""

import logging
import time

logger = logging.getLogger(__name__)

try:
    from app.celery_app import celery_app

    @celery_app.task(name="app.tasks.heartbeat.worker_heartbeat")
    def worker_heartbeat():
        """Write worker heartbeat timestamp to Redis."""
        from app.redis_client import get_redis_client

        redis_client = get_redis_client()
        if redis_client:
            try:
                redis_client.set("celery:worker:heartbeat", time.time(), ex=600)
                logger.debug("Worker heartbeat written")
            except Exception as exc:
                logger.warning("Failed to write worker heartbeat: %s", exc)

    @celery_app.task(name="app.tasks.heartbeat.beat_heartbeat")
    def beat_heartbeat():
        """Write beat heartbeat timestamp to Redis."""
        from app.redis_client import get_redis_client

        redis_client = get_redis_client()
        if redis_client:
            try:
                redis_client.set("celery:beat:heartbeat", time.time(), ex=600)
                logger.debug("Beat heartbeat written")
            except Exception as exc:
                logger.warning("Failed to write beat heartbeat: %s", exc)

    # Register periodic tasks
    from celery.schedules import crontab

    celery_app.conf.beat_schedule = celery_app.conf.beat_schedule or {}
    celery_app.conf.beat_schedule.update({
        "worker-heartbeat": {
            "task": "app.tasks.heartbeat.worker_heartbeat",
            "schedule": 60.0,  # every minute
        },
        "beat-heartbeat": {
            "task": "app.tasks.heartbeat.beat_heartbeat",
            "schedule": 60.0,  # every minute
        },
    })

except Exception:
    # Celery not configured — tasks will not be registered
    pass