from types import SimpleNamespace

from fastapi import Request, Response
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter

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


def _rate_limiter_request(request: Request) -> Request:
    if "app" not in request.scope:
        return request

    routes = []
    for route in request.app.routes:
        if hasattr(route, "path") and hasattr(route, "methods"):
            routes.append(route)
            continue

        effective_route_contexts = getattr(route, "effective_route_contexts", None)
        if effective_route_contexts is None:
            continue

        routes.extend(
            nested_route
            for nested_route in effective_route_contexts()
            if hasattr(nested_route, "path") and hasattr(nested_route, "methods")
        )

    scope = dict(request.scope)
    scope["app"] = SimpleNamespace(routes=routes)
    return Request(scope, receive=request.receive)


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


async def apply_global_rate_limit(request: Request, response: Response):
    if request.url.path in EXEMPT_PATHS:
        return

    limit_str = settings.RATE_LIMIT
    times_str, period = limit_str.split("/")
    times = int(times_str)
    seconds = 60 if "minute" in period else 1

    limiter = RateLimiter(times=times, seconds=seconds)
    await limiter(_rate_limiter_request(request), response)
