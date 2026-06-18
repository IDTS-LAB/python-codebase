import hashlib
import json

from fastapi import Request, status
from fastapi.responses import JSONResponse, Response
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

        request_body = await request.body()
        request_body_hash = hashlib.sha256(request_body).hexdigest()
        redis = self._redis or await get_redis_client()
        cache_key = self._cache_key(request, idempotency_key)

        cached = await redis.get(cache_key)
        if cached:
            cached_response = json.loads(cached)
            if cached_response.get("request_body_hash") != request_body_hash:
                return JSONResponse(
                    status_code=status.HTTP_409_CONFLICT,
                    content={
                        "detail": (
                            "Idempotency-Key was already used with a different "
                            "request body"
                        )
                    },
                )
            return Response(
                content=cached_response["body"],
                status_code=cached_response["status_code"],
                media_type=cached_response.get("media_type"),
                headers={"X-Idempotent-Replay": "true"},
            )

        request = self._rebuild_request(request, request_body)
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
                        "request_body_hash": request_body_hash,
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
    def _rebuild_request(request: Request, body: bytes) -> Request:
        async def receive():
            return {"type": "http.request", "body": body, "more_body": False}

        return Request(request.scope, receive)

    @staticmethod
    async def _response_body(response) -> bytes:
        if hasattr(response, "body"):
            return response.body

        body = b""
        async for chunk in response.body_iterator:
            body += chunk
        return body
