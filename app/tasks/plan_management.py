"""Plan management Celery tasks."""

from app.celery_app import celery_app


@celery_app.task
def downgrade_expired_trials():
    """Run daily to downgrade expired trials to free plan."""
    from app.models import PoliceUser
    from app.extensions import db
    from datetime import datetime, timezone

    users = PoliceUser.query.filter(
        PoliceUser.plan_type == 'trial',
        PoliceUser.trial_ends_at < datetime.now(timezone.utc),
    ).all()

    for user in users:
        user.plan_type = 'free'
        user.trial_ends_at = None
        db.session.add(user)

    db.session.commit()
    return len(users)
