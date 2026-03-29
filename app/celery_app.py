"""Celery application factory.

Usage (start worker):
    celery -A app.celery_app worker --loglevel=info

Usage (start beat scheduler):
    celery -A app.celery_app beat --loglevel=info
"""

import os
import time
from celery import Celery
from celery.schedules import crontab

broker = os.environ.get("CELERY_BROKER_URL", "")
backend = os.environ.get("CELERY_RESULT_BACKEND", "")

celery_app = Celery(
    "saladetriagem",
    broker=broker or None,
    backend=backend or None,
    include=[
        "app.tasks.session_expiry",
        "app.tasks.cleanup",
        "app.tasks.heartbeat",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="America/Sao_Paulo",
    enable_utc=True,
    # Scheduled tasks
    beat_schedule={
        "expire-sessions-every-5-minutes": {
            "task": "app.tasks.session_expiry.expire_sessions",
            "schedule": 300,  # every 5 minutes
        },
        "cleanup-orphan-photos-hourly": {
            "task": "app.tasks.cleanup.cleanup_orphan_photos",
            "schedule": 3600,  # every 1 hour
        },
        "cleanup-old-access-logs-daily": {
            "task": "app.tasks.cleanup.cleanup_old_access_logs",
            "schedule": crontab(hour=3, minute=0),  # 3am
        },
    },
)


@celery_app.on_after_configure.connect
def update_beat_heartbeat(sender, **kwargs):  # noqa: ARG001
    """Record a lightweight heartbeat from Celery Beat startup/config time."""
    try:
        from app.redis_client import get_redis_client

        redis_client = get_redis_client()
        if redis_client:
            redis_client.set("celery:beat:heartbeat", str(time.time()), ex=300)
    except Exception:
        pass


@celery_app.on_after_finalize.connect
def setup_periodic_beat_marker(sender, **kwargs):  # noqa: ARG001
    """Refresh beat heartbeat periodically from the beat process itself."""
    try:
        from app.redis_client import get_redis_client

        def _mark_beat_alive():
            redis_client = get_redis_client()
            if redis_client:
                redis_client.set("celery:beat:heartbeat", str(time.time()), ex=300)

        sender.add_periodic_task(60.0, _beat_marker_task.s(), name="beat-self-heartbeat")
    except Exception:
        pass


@celery_app.task(name="app.celery_app._beat_marker_task")
def _beat_marker_task():
    """Scheduled by beat to confirm beat scheduling is active."""
    try:
        from app.redis_client import get_redis_client

        redis_client = get_redis_client()
        if redis_client:
            redis_client.set("celery:beat:heartbeat", str(time.time()), ex=300)
            return True
    except Exception:
        pass
    return False