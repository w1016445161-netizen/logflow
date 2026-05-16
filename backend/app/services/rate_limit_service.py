from dataclasses import dataclass

from redis import RedisError

from app.core.config import settings
from app.core.redis_client import get_redis_client


@dataclass
class RateLimitResult:
    limited: bool
    current_count: int
    limit: int
    window_seconds: int
    key: str
    reason: str | None = None


def check_rate_limit(client_id: str | None, ip: str | None) -> RateLimitResult:
    if client_id:
        key = f"logflow:rate_limit:client:{client_id}"
    elif ip:
        key = f"logflow:rate_limit:ip:{ip}"
    else:
        key = "logflow:rate_limit:anonymous"

    limit = settings.RATE_LIMIT_MAX_REQUESTS
    window = settings.RATE_LIMIT_WINDOW_SECONDS

    if not settings.RATE_LIMIT_ENABLED:
        return RateLimitResult(
            limited=False, current_count=0, limit=limit, window_seconds=window, key=key,
        )

    try:
        r = get_redis_client()
        current = r.incr(key)
        if current == 1:
            r.expire(key, window)

        return RateLimitResult(
            limited=current > limit,
            current_count=current,
            limit=limit,
            window_seconds=window,
            key=key,
        )
    except RedisError:
        return RateLimitResult(
            limited=False, current_count=0, limit=limit, window_seconds=window, key=key, reason="redis_error",
        )
