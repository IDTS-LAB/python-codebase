import time

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from src.core.telemetry.metrics import ACTIVE_REQUESTS, REQUEST_COUNT, REQUEST_LATENCY

EXCLUDED_PATHS = frozenset({"/metrics", "/health", "/live", "/ready"})


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        if request.url.path in EXCLUDED_PATHS:
            return await call_next(request)

        ACTIVE_REQUESTS.inc()
        start = time.perf_counter()
        status_code = 500

        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        finally:
            latency = time.perf_counter() - start
            ACTIVE_REQUESTS.dec()
            REQUEST_COUNT.labels(
                method=request.method,
                endpoint=request.url.path,
                http_status=str(status_code),
            ).inc()
            REQUEST_LATENCY.labels(
                method=request.method,
                endpoint=request.url.path,
            ).observe(latency)
