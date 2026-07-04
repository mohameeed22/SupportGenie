from __future__ import annotations

import json
import logging
from typing import Any

import config

logger = logging.getLogger(__name__)

_client = None


def _get_client():
    global _client
    if _client is None and config.REDIS_URL:
        try:
            import redis.asyncio as aioredis

            _client = aioredis.from_url(config.REDIS_URL, decode_responses=True)
            logger.info("Connected to Redis at %s", config.REDIS_URL)
        except Exception as exc:
            logger.warning("Redis connection failed (%s), caching disabled", exc)
            _client = False
    elif _client is None:
        _client = False
    return _client if _client else None


async def cache_get(key: str) -> str | None:
    client = _get_client()
    if not client:
        return None
    try:
        return await client.get(key)
    except Exception:
        return None


async def cache_set(key: str, value: str, ttl: int = 300) -> None:
    client = _get_client()
    if not client:
        return
    try:
        await client.setex(key, ttl, value)
    except Exception:
        pass


async def cache_delete(key: str) -> None:
    client = _get_client()
    if not client:
        return
    try:
        await client.delete(key)
    except Exception:
        pass


async def cache_order(order_id: str, order_data: dict, ttl: int = 600) -> None:
    await cache_set(f"order:{order_id}", json.dumps(order_data), ttl=ttl)


async def get_cached_order(order_id: str) -> dict | None:
    raw = await cache_get(f"order:{order_id}")
    if raw:
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            pass
    return None


async def increment_rate_limit(user_id: int, window: int = 60) -> int:
    client = _get_client()
    if not client:
        return 0
    key = f"ratelimit:{user_id}"
    try:
        count = await client.incr(key)
        if count == 1:
            await client.expire(key, window)
        return count
    except Exception:
        return 0
