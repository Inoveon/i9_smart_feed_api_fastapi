from __future__ import annotations

import os
import json
from functools import wraps

import redis


def get_redis():
    url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    return redis.from_url(url)


def cache(expire: int = 300, key_prefix: str = "cache"):
    client = get_redis()

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            key = f"{key_prefix}:{':'.join(map(str, args))}:{':'.join(f'{k}={v}' for k, v in kwargs.items())}"
            try:
                cached = client.get(key)
                if cached:
                    return json.loads(cached)
            except Exception:
                # Sem Redis, segue sem cache
                pass
            result = await func(*args, **kwargs)
            try:
                client.setex(key, expire, json.dumps(result, default=str))
            except Exception:
                pass
            return result

        return wrapper

    return decorator


def invalidate(pattern: str):
    client = get_redis()
    try:
        for key in client.scan_iter(match=pattern):
            client.delete(key)
    except Exception:
        # Sem Redis, nada a invalidar
        pass
