# src/core/rate_limiter.py
import redis.asyncio as redis

from src.core.config.setting import get_settings

redis_client: redis.Redis | None = None

settings = get_settings()


async def get_redis_client() -> redis.Redis:
    global redis_client
    if redis_client is None:
        redis_client = redis.from_url(
            settings.REDIS_URL, encoding="utf-8", decode_responses=True
        )
    return redis_client
