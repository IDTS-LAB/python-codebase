import logging
import time

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class StructuredLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        started_at = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception as exc:
            self._log_request(
                request=request,
                started_at=started_at,
                status_code=500,
                level=logging.ERROR,
                message="request failed",
                error_type=type(exc).__name__,
            )
            raise

        self._log_request(
            request=request,
            started_at=started_at,
            status_code=response.status_code,
            level=logging.INFO,
            message="request completed",
        )
        return response

    @staticmethod
    def _log_request(
        request: Request,
        started_at: float,
        status_code: int,
        level: int,
        message: str,
        error_type: str | None = None,
    ) -> None:
        latency_ms = round((time.perf_counter() - started_at) * 1000, 2)
        logger.log(
            level,
            message,
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": status_code,
                "latency_ms": latency_ms,
                "request_id": getattr(request.state, "request_id", None),
                "user_id": getattr(request.state, "user_id", None),
                "error_type": error_type,
            },
        )
