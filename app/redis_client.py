"""Redis connection manager with graceful fallback.

If Redis is unavailable (REDIS_URL not configured or server unreachable),
all callers receive ``None`` and should fall back to in-memory behaviour.
"""

import logging
import os

logger = logging.getLogger(__name__)

_redis_client = None
_initialized = False


def get_redis_client():
    """Return a connected Redis client, or *None* if unavailable."""
    global _redis_client, _initialized

    if _initialized:
        return _redis_client

    _initialized = True
    url = os.environ.get("REDIS_URL", "")
    if not url:
        logger.info("REDIS_URL not configured — using in-memory fallback")
        return None

    try:
        import redis

        client = redis.from_url(
            url,
            socket_connect_timeout=2,
            socket_timeout=2,
            retry_on_timeout=True,
            health_check_interval=30,
            decode_responses=False,
        )
        client.ping()
        _redis_client = client
        logger.info("Redis connected: %s", url.split("@")[-1])
    except Exception as exc:  # pragma: no cover
        logger.warning("Redis unavailable (%s) — using in-memory fallback", exc)
        _redis_client = None

    return _redis_client


def reset_redis_client():
    """Reset cached client — useful for testing."""
    global _redis_client, _initialized
    _redis_client = None
    _initialized = False
