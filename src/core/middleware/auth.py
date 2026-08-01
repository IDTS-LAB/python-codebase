from typing import Optional

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from src.core.security.providers import (
    AuthenticationProvider,
    JWTAuthProvider,
)

PUBLIC_PATHS = frozenset(
    {
        "/health",
        "/live",
        "/ready",
        "/metrics",
        "/docs",
        "/docs/",
        "/redoc",
        "/redoc/",
        "/openapi.json",
        "/api/v1/auth/login",
        "/api/v1/auth/register",
        "/api/v1/auth/refresh",
    }
)


class AuthenticationMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, providers: Optional[list[AuthenticationProvider]] = None):
        super().__init__(app)
        self._providers = providers or [JWTAuthProvider()]

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        if request.method == "OPTIONS":
            return await call_next(request)

        path = request.url.path.rstrip("/")
        if path in PUBLIC_PATHS:
            return await call_next(request)

        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={"detail": "Authorization header missing or malformed"},
            )

        token = auth_header.split(" ", 1)[1]

        for provider in self._providers:
            result = await provider.authenticate(token, request)
            if result is not None:
                request.state.user_id = result["user_id"]
                request.state.auth_provider = result["provider"]
                request.state.token_payload = result.get("payload", {})
                response = await call_next(request)
                return response

        return JSONResponse(
            status_code=401,
            content={"detail": "Invalid or expired token"},
        )
