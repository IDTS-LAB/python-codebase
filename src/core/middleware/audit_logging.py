import logging
import traceback as traceback_module
from collections.abc import Callable

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from src.core.database.postgres.session import AsyncSessionLocal
from src.core.security.audit import (
    AuditEvent,
    AuditService,
    ErrorTrace,
    ErrorTraceService,
)
from src.core.security.infrastructure.repositories.audit_log_repository import (
    SQLAlchemyAuditRepository,
)
from src.core.security.infrastructure.repositories.error_trace_repository import (
    SQLAlchemyErrorTraceRepository,
)

logger = logging.getLogger(__name__)

EXCLUDED_AUDIT_PATHS = frozenset(
    {
        "/health",
        "/live",
        "/ready",
        "/docs",
        "/docs/",
        "/redoc",
        "/redoc/",
        "/openapi.json",
    }
)


class AuditLoggingMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        audit_service_factory: Callable[[], AuditService] | None = None,
        error_trace_service_factory: Callable[[], ErrorTraceService] | None = None,
    ):
        super().__init__(app)
        self._audit_service_factory = audit_service_factory
        self._error_trace_service_factory = error_trace_service_factory

    async def dispatch(self, request: Request, call_next):
        if self._is_excluded(request):
            return await call_next(request)

        try:
            response = await call_next(request)
        except Exception as exc:
            await self._record_error_trace(request, exc)
            raise

        await self._record_audit_event(request, response.status_code)
        return response

    def _is_excluded(self, request: Request) -> bool:
        return request.url.path.rstrip("/") in {
            path.rstrip("/") for path in EXCLUDED_AUDIT_PATHS
        }

    async def _record_audit_event(self, request: Request, status_code: int) -> None:
        event = AuditEvent(
            action=f"{request.method} {request.url.path}",
            actor_id=getattr(request.state, "user_id", None),
            resource_type=self._resource_type(request),
            resource_id=self._resource_id(request),
            request_id=getattr(request.state, "request_id", None),
            metadata={
                "method": request.method,
                "path": request.url.path,
                "status_code": status_code,
                "client_ip": self._client_ip(request),
                "user_agent": request.headers.get("User-Agent"),
            },
        )
        await self._safe_record_audit(event)

    async def _record_error_trace(self, request: Request, exc: Exception) -> None:
        trace = ErrorTrace(
            error_type=type(exc).__name__,
            message=str(exc),
            traceback=traceback_module.format_exc(),
            method=request.method,
            path=request.url.path,
            actor_id=getattr(request.state, "user_id", None),
            request_id=getattr(request.state, "request_id", None),
            metadata={
                "client_ip": self._client_ip(request),
                "user_agent": request.headers.get("User-Agent"),
            },
        )
        await self._safe_record_error_trace(trace)

    async def _safe_record_audit(self, event: AuditEvent) -> None:
        try:
            factory = self._audit_service_factory or self._default_audit_service_factory
            service = factory()
            await service.record(event)
        except Exception:
            logger.exception("failed to record audit event")

    async def _safe_record_error_trace(self, trace: ErrorTrace) -> None:
        try:
            factory = (
                self._error_trace_service_factory
                or self._default_error_trace_service_factory
            )
            service = factory()
            await service.record(trace)
        except Exception:
            logger.exception("failed to record error trace")

    def _default_audit_service_factory(self) -> AuditService:
        return _SessionBackedAuditService()

    def _default_error_trace_service_factory(self) -> ErrorTraceService:
        return _SessionBackedErrorTraceService()

    @staticmethod
    def _resource_type(request: Request) -> str | None:
        parts = [part for part in request.url.path.split("/") if part]
        if len(parts) >= 3 and parts[0] == "api" and parts[1].startswith("v"):
            return parts[2]
        return parts[0] if parts else None

    @staticmethod
    def _resource_id(request: Request) -> str | None:
        for key in ("id", "todo_id", "role_id", "permission_id", "user_id"):
            if key in request.path_params:
                return str(request.path_params[key])
        return None

    @staticmethod
    def _client_ip(request: Request) -> str | None:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else None


class _SessionBackedAuditService(AuditService):
    async def record(self, event: AuditEvent) -> None:
        async with AsyncSessionLocal() as session:
            repository = SQLAlchemyAuditRepository(session)
            await repository.save(event)
            await session.commit()


class _SessionBackedErrorTraceService(ErrorTraceService):
    async def record(self, trace: ErrorTrace) -> None:
        async with AsyncSessionLocal() as session:
            repository = SQLAlchemyErrorTraceRepository(session)
            await repository.save(trace)
            await session.commit()
