from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from src.core.config.setting import get_settings

settings = get_settings()
_default_tenant_id: int | None = None


def set_default_tenant_id(tenant_id: int) -> None:
    global _default_tenant_id
    _default_tenant_id = tenant_id


class TenantMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        if not settings.MULTITENANT_ENABLED:
            request.state.tenant_id = _default_tenant_id
            return await call_next(request)

        if request.method == "OPTIONS":
            return await call_next(request)

        path = request.url.path.rstrip("/")
        public_paths = {"/health", "/live", "/ready", "/metrics", "/docs", "/redoc", "/openapi.json"}
        if path in public_paths:
            return await call_next(request)

        from sqlalchemy import select

        from src.core.database.postgres.session import AsyncSessionLocal
        from src.modules.tenants.infrastructure.models.tenant_model import TenantModel

        tenant_header = request.headers.get("X-Tenant-ID")
        if tenant_header:
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(TenantModel.id).where(TenantModel.slug == tenant_header)
                )
                tid = result.scalar_one_or_none()
            if tid is not None:
                request.state.tenant_id = tid
                return await call_next(request)

        host = request.headers.get("host", "")
        if host and "." in host and host.count(".") >= 2:
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(TenantModel.id).where(TenantModel.domain == host)
                )
                tid = result.scalar_one_or_none()
            if tid is not None:
                request.state.tenant_id = tid
                return await call_next(request)

        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            from jose import jwt as jose_jwt

            try:
                payload = jose_jwt.decode(
                    auth_header.split(" ", 1)[1],
                    settings.SECRET_KEY,
                    algorithms=[settings.ALGORITHM],
                    options={"verify_aud": False},
                )
                tid = payload.get("tenant_id")
                if tid:
                    request.state.tenant_id = int(tid) if isinstance(tid, str) else tid
                    return await call_next(request)
            except Exception:
                pass

        return JSONResponse(
            status_code=400,
            content={"detail": "Tenant not identified. Provide X-Tenant-ID header."},
        )
