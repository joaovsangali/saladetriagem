"""Celery application factory.

Usage (start worker):
    celery -A app.celery_app worker --loglevel=info

Usage (start beat scheduler):
    celery -A app.celery_app beat --loglevel=info
"""

import os
from celery import Celery
from celery.schedules import crontab

broker = os.environ.get("CELERY_BROKER_URL", "")
backend = os.environ.get("CELERY_RESULT_BACKEND", "")

celery_app = Celery(
    "saladetriagem",
    broker=broker or None,
    backend=backend or None,
    include=["app.tasks.session_expiry", "app.tasks.cleanup"],
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
