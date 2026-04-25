"""Centralized plan feature helpers for Sala de Triagem.

Use these helpers instead of scattering plan-check logic across templates
and routes.  All plan-gating decisions should go through here so that
adding or changing a plan only requires touching this file (and plans.py).
"""

import logging

logger = logging.getLogger(__name__)


def _effective_plan(user) -> str:
    """Return the effective plan key for the given user."""
    from app.plans import PLANS
    if user.is_trial_active():
        return 'trial'
    plan = getattr(user, 'plan_type', 'free')
    return plan if plan in PLANS else 'free'


def get_plan_limits(user) -> dict:
    """Return the limits dict for the user's current effective plan."""
    return user.get_current_plan_limits()


def can_share_session(user) -> bool:
    """Return True if the user can create and share session join codes.

    Only Enterprise users can generate join codes.  Premium users can
    *join* shared sessions but cannot create codes themselves.
    """
    try:
        limits = user.get_current_plan_limits()
        return bool(limits.get('can_share_session', False))
    except Exception:
        logger.exception("plan_helpers.can_share_session failed for user %s", getattr(user, 'id', '?'))
        return False


def can_join_shared_session(user) -> bool:
    """Return True if the user can join a session via a join code.

    Premium and Enterprise users can join shared sessions.
    Free users cannot.
    """
    try:
        limits = user.get_current_plan_limits()
        return bool(limits.get('can_join_shared_session', False))
    except Exception:
        logger.exception("plan_helpers.can_join_shared_session failed for user %s", getattr(user, 'id', '?'))
        return False


def can_create_custom_schema(user) -> bool:
    """Return True if the user can create custom intake templates.

    Only Enterprise users have access to custom schemas.
    """
    try:
        limits = user.get_current_plan_limits()
        return bool(limits.get('can_create_custom_schema', False))
    except Exception:
        logger.exception("plan_helpers.can_create_custom_schema failed for user %s", getattr(user, 'id', '?'))
        return False
