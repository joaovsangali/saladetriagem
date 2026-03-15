"""Per-user / per-IP rate limiting helpers.

These utilities complement Flask-Limiter's global limits by providing
more granular control based on form submission context.
"""

import logging
import time
import threading
from typing import Dict, Tuple

logger = logging.getLogger(__name__)


class InMemoryRateLimiter:
    """Simple sliding-window rate limiter for use without Redis."""

    def __init__(self):
        self._lock = threading.Lock()
        # key -> list of timestamps
        self._buckets: Dict[str, list] = {}

    def is_allowed(self, key: str, limit: int, window_seconds: int) -> bool:
        """Return True if *key* has not exceeded *limit* requests in *window_seconds*."""
        now = time.monotonic()
        cutoff = now - window_seconds
        with self._lock:
            bucket = self._buckets.get(key, [])
            # Remove old entries
            bucket = [t for t in bucket if t > cutoff]
            if len(bucket) >= limit:
                self._buckets[key] = bucket
                return False
            bucket.append(now)
            self._buckets[key] = bucket
            return True


_memory_limiter = InMemoryRateLimiter()


def check_submission_rate(
    user_identifier: str,
    ip_address: str,
    limit: int = 5,
    window_seconds: int = 60,
) -> bool:
    """Return True if the submission should be allowed, False to throttle.

    Checks both the user identifier (token-based) and IP address.
    Uses Redis when available, falls back to in-memory.
    """
    try:
        from app.redis_client import get_redis_client

        redis = get_redis_client()
        if redis is not None:
            return _redis_check(redis, user_identifier, ip_address, limit, window_seconds)
    except Exception as exc:
        logger.debug("Redis rate limit check failed, falling back: %s", exc)

    # In-memory fallback
    key_user = f"rl:submit:{user_identifier}"
    key_ip = f"rl:submit:ip:{ip_address}"
    return _memory_limiter.is_allowed(key_user, limit, window_seconds) and \
           _memory_limiter.is_allowed(key_ip, limit * 3, window_seconds)


def _redis_check(
    redis,
    user_identifier: str,
    ip_address: str,
    limit: int,
    window_seconds: int,
) -> bool:
    """Sliding-window rate limit check using Redis sorted sets."""
    now = time.time()
    cutoff = now - window_seconds

    for key, max_requests in [
        (f"rl:submit:{user_identifier}", limit),
        (f"rl:submit:ip:{ip_address}", limit * 3),
    ]:
        pipe = redis.pipeline()
        pipe.zremrangebyscore(key, "-inf", cutoff)
        pipe.zcard(key)
        pipe.zadd(key, {str(now): now})
        pipe.expire(key, window_seconds * 2)
        results = pipe.execute()
        count = results[1]
        if count >= max_requests:
            return False
    return True
