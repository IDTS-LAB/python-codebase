from fastapi import HTTPException, Request
from fastapi_limiter import FastAPILimiter

from src.core.config.setting import get_settings
from src.core.database.redis.client import get_redis_client

EXEMPT_PATHS = frozenset(
    {
        "/health",
        "/docs",
        "/docs/",
        "/redoc",
        "/redoc/",
        "/openapi.json",
    }
)


settings = get_settings()


async def custom_identifier(request: Request) -> str:
    """Smart identifier: User ID > Proxy IP > Direct IP"""
    user_id = getattr(request.state, "user_id", None)
    if user_id:
        return f"user:{user_id}"

    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return f"ip:{forwarded.split(',')[0].strip()}"

    if request.client and request.client.host:
        return f"ip:{request.client.host}"

    return "unknown"


async def init_rate_limiter():
    r = await get_redis_client()
    await FastAPILimiter.init(r, identifier=custom_identifier)


async def close_rate_limiter():
    redis_client = await get_redis_client()
    await redis_client.aclose()


async def apply_global_rate_limit(request: Request):
    if request.url.path in EXEMPT_PATHS:
        return

    limit_str = settings.RATE_LIMIT
    times_str, period = limit_str.split("/")
    times = int(times_str)
    seconds = 60 if "minute" in period else 1

    # Get identifier for this request
    identifier = await custom_identifier(request)

    # Check rate limit
    is_rate_limited = await FastAPILimiter.redis.incr(
        f"fastapi-limiter:{identifier}:{request.scope.get('path')}"
    )

    # Set expiry on first request
    if is_rate_limited == 1:
        await FastAPILimiter.redis.expire(
            f"fastapi-limiter:{identifier}:{request.scope.get('path')}", seconds
        )

    # Check if rate limit exceeded
    if is_rate_limited > times:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
