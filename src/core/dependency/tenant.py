from uuid import UUID

from fastapi import HTTPException, Request
from starlette.status import HTTP_400_BAD_REQUEST


def get_current_tenant_id(request: Request) -> UUID:
    tenant_id: UUID | None = getattr(request.state, "tenant_id", None)
    if tenant_id is None:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="Tenant not identified",
        )
    return tenant_id


def get_optional_tenant_id(request: Request) -> UUID | None:
    return getattr(request.state, "tenant_id", None)
