import json
from typing import Any, Callable
from redis import RedisError
from app.core.redis_client import get_redis_client


def get_cached_or_compute(cache_key: str, ttl: int, compute_func: Callable[[], Any]) -> Any:
    try:
        r = get_redis_client()
        cached = r.get(cache_key)
        if cached is not None:
            return json.loads(cached)
    except (RedisError, json.JSONDecodeError):
        pass

    data = compute_func()

    try:
        r = get_redis_client()
        r.setex(cache_key, ttl, json.dumps(data, default=str))
    except (RedisError, TypeError):
        pass

    return data
