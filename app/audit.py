"""Audit logging helper — records every access to sensitive submission data."""
import logging

from flask import request

from app.extensions import db
from app.models import AccessLog

logger = logging.getLogger(__name__)


def log_access(user, submission_id: str | None, action: str) -> None:
    """Record an audit entry. Failures are logged but never raise."""
    try:
        entry = AccessLog(
            user_id=user.id,
            submission_id=submission_id,
            action=action,
            ip_address=request.remote_addr,
            user_agent=(request.headers.get("User-Agent", "") or "")[:256],
        )
        db.session.add(entry)
        db.session.commit()
    except Exception as exc:
        logger.error("Falha ao registrar access log: %s", exc, exc_info=True)
        db.session.rollback()
