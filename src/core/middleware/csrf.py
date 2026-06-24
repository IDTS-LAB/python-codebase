from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from src.core.config.setting import get_settings
from src.core.security.csrf import CSRFService, DoubleSubmitCSRFService

CSRF_COOKIE_NAME = "csrf_token"
CSRF_HEADER_NAME = "X-CSRF-Token"

SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS", "TRACE"})

_settings = get_settings()


class CSRFMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, service: CSRFService | None = None):
        super().__init__(app)
        self._service = service or DoubleSubmitCSRFService()

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        if not _settings.CSRF_PROTECTION_ENABLED:
            return await call_next(request)

        if request.method in SAFE_METHODS:
            response = await call_next(request)
            cookie_token = request.cookies.get(CSRF_COOKIE_NAME)
            if not cookie_token:
                response.set_cookie(
                    key=CSRF_COOKIE_NAME,
                    value=self._service.generate_token(),
                    httponly=True,
                    samesite="strict",
                    secure=request.url.scheme == "https",
                    max_age=86400,
                )
            return response

        header_token = request.headers.get(CSRF_HEADER_NAME, "")
        cookie_token = request.cookies.get(CSRF_COOKIE_NAME, "")

        if not self._service.validate_token(header_token, cookie_token):
            return JSONResponse(
                status_code=403,
                content={"detail": "CSRF token missing or invalid"},
            )

        return await call_next(request)
