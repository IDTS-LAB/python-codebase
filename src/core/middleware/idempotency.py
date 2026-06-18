import hashlib
import json

from fastapi import Request
from fastapi.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware

from src.core.config.setting import get_settings
from src.core.database.redis.client import get_redis_client

settings = get_settings()


class IdempotencyMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, redis=None):
        super().__init__(app)
        self._redis = redis

    async def dispatch(self, request: Request, call_next):
        if request.method != "POST":
            return await call_next(request)

        idempotency_key = request.headers.get("Idempotency-Key")
        if not idempotency_key:
            return await call_next(request)

        redis = self._redis or await get_redis_client()
        cache_key = self._cache_key(request, idempotency_key)

        cached = await redis.get(cache_key)
        if cached:
            cached_response = json.loads(cached)
            return Response(
                content=cached_response["body"],
                status_code=cached_response["status_code"],
                media_type=cached_response.get("media_type"),
                headers={"X-Idempotent-Replay": "true"},
            )

        response = await call_next(request)
        body = await self._response_body(response)

        if 200 <= response.status_code < 300:
            await redis.setex(
                cache_key,
                settings.IDEMPOTENCY_TTL_SECONDS,
                json.dumps(
                    {
                        "body": body.decode(),
                        "status_code": response.status_code,
                        "media_type": response.media_type,
                    }
                ),
            )

        return Response(
            content=body,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.media_type,
        )

    @staticmethod
    def _cache_key(request: Request, idempotency_key: str) -> str:
        auth_scope = request.headers.get("Authorization", "anonymous")
        raw = f"{auth_scope}:{request.url.path}:{idempotency_key}"
        digest = hashlib.sha256(raw.encode()).hexdigest()
        return f"idempotency:{digest}"

    @staticmethod
    async def _response_body(response) -> bytes:
        if hasattr(response, "body"):
            return response.body

        body = b""
        async for chunk in response.body_iterator:
            body += chunk
        return body
