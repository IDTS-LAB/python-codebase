from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.core.database.postgres.session import get_unit_of_work
from src.core.schemas.response import (
    CursorMeta,
    CursorPaginatedResponse,
    SuccessResponse,
)
from src.modules.authorization.domain.entities.role import Role
from src.modules.authorization.domain.permissions import (
    CREATE_ACTION,
    DELETE_ACTION,
    READ_ACTION,
    ROLE_RESOURCE,
    UPDATE_ACTION,
)
from src.modules.authorization.infrastructure.services.casbin_authorization_service import (
    CasbinAuthorizationService,
)
from src.modules.authorization.presentation.dependency import (
    get_authorization_service,
    require_permission,
)
from src.modules.authorization.presentation.schema.request import (
    CreateRoleRequest,
    UpdateRoleRequest,
)
from src.modules.authorization.presentation.schema.response import RoleResponse
from src.shared.unit_of_work import UnitOfWork
from src.shared.utils.cursor import CursorDirection, decode_cursor, encode_cursor

router = APIRouter(prefix="/roles", tags=["Role"])


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=SuccessResponse[RoleResponse],
    dependencies=[Depends(require_permission(ROLE_RESOURCE, CREATE_ACTION))],
)
async def create_role(
    request: CreateRoleRequest,
    service: CasbinAuthorizationService = Depends(get_authorization_service),
    unit_of_work: UnitOfWork = Depends(get_unit_of_work),
):
    role = Role.create(name=request.name, description=request.description)
    async with unit_of_work:
        created = await service.create_role(role)
        await unit_of_work.commit()
    return SuccessResponse(
        message="create role success", success=True, data=_role_response(created)
    )


@router.get(
    "/",
    response_model=CursorPaginatedResponse[RoleResponse],
    dependencies=[Depends(require_permission(ROLE_RESOURCE, READ_ACTION))],
)
async def list_roles(
    cursor: Optional[str] = Query(
        None, description="Cursor for pagination (from previous response)"
    ),
    limit: int = Query(10, ge=1, le=100, description="Number of items per page"),
    service: CasbinAuthorizationService = Depends(get_authorization_service),
):
    cursor_created_at = None
    cursor_id = None
    direction = CursorDirection.DIRECTION_NEXT
    if cursor:
        cursor_created_at, cursor_id, direction = decode_cursor(cursor)

    roles, has_more = await service.list_roles_cursor(
        cursor_created_at=cursor_created_at,
        cursor_id=cursor_id,
        limit=limit,
        direction=direction,
    )

    next_cursor = None
    prev_cursor = None

    if has_more and roles:
        last_item = roles[-1]
        next_cursor = encode_cursor(
            _created_at_datetime(last_item.created_at),
            last_item.id,
            CursorDirection.DIRECTION_NEXT,
        )

    if cursor and roles:
        first_item = roles[0]
        prev_cursor = encode_cursor(
            _created_at_datetime(first_item.created_at),
            first_item.id,
            CursorDirection.DIRECTION_PREV,
        )

    return CursorPaginatedResponse(
        message="fetch role success",
        success=True,
        data=[_role_response(role) for role in roles],
        meta=CursorMeta(
            next_cursor=next_cursor,
            prev_cursor=prev_cursor,
            has_next=has_more,
            has_prev=cursor is not None,
            limit=limit,
        ),
    )


@router.get(
    "/{role_id}",
    response_model=SuccessResponse[RoleResponse],
    dependencies=[Depends(require_permission(ROLE_RESOURCE, READ_ACTION))],
)
async def get_role(
    role_id: UUID,
    service: CasbinAuthorizationService = Depends(get_authorization_service),
):
    role = await service.get_role(role_id)
    if role is None:
        raise HTTPException(status_code=404, detail="Role not found")
    return SuccessResponse(
        message="fetch role success", success=True, data=_role_response(role)
    )


@router.patch(
    "/{role_id}",
    response_model=SuccessResponse[RoleResponse],
    dependencies=[Depends(require_permission(ROLE_RESOURCE, UPDATE_ACTION))],
)
async def update_role(
    role_id: UUID,
    request: UpdateRoleRequest,
    service: CasbinAuthorizationService = Depends(get_authorization_service),
    unit_of_work: UnitOfWork = Depends(get_unit_of_work),
):
    existing = await service.get_role(role_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="Role not found")

    role = Role(
        id=role_id,
        name=request.name if request.name is not None else existing.name,
        description=(
            request.description
            if request.description is not None
            else existing.description
        ),
    )
    async with unit_of_work:
        updated = await service.update_role(role)
        await unit_of_work.commit()
    return SuccessResponse(
        message="update role success", success=True, data=_role_response(updated)
    )


@router.delete(
    "/{role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission(ROLE_RESOURCE, DELETE_ACTION))],
)
async def delete_role(
    role_id: UUID,
    service: CasbinAuthorizationService = Depends(get_authorization_service),
    unit_of_work: UnitOfWork = Depends(get_unit_of_work),
):
    async with unit_of_work:
        await service.delete_role(role_id)
        await unit_of_work.commit()


@router.post(
    "/{role_id}/permissions/{permission_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission(ROLE_RESOURCE, CREATE_ACTION))],
)
async def assign_permission_to_role(
    role_id: UUID,
    permission_id: UUID,
    service: CasbinAuthorizationService = Depends(get_authorization_service),
    unit_of_work: UnitOfWork = Depends(get_unit_of_work),
):
    async with unit_of_work:
        await service.assign_permission_to_role(role_id, permission_id)
        await unit_of_work.commit()


@router.delete(
    "/{role_id}/permissions/{permission_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission(ROLE_RESOURCE, DELETE_ACTION))],
)
async def remove_permission_from_role(
    role_id: UUID,
    permission_id: UUID,
    service: CasbinAuthorizationService = Depends(get_authorization_service),
    unit_of_work: UnitOfWork = Depends(get_unit_of_work),
):
    async with unit_of_work:
        await service.remove_permission_from_role(role_id, permission_id)
        await unit_of_work.commit()


def _role_response(role: Role | None) -> RoleResponse:
    if role is None:
        raise HTTPException(status_code=404, detail="Role not found")

    return RoleResponse(
        id=str(role.id),
        name=role.name,
        description=role.description,
        created_at=role.created_at,
        updated_at=role.updated_at,
    )


def _created_at_datetime(created_at: datetime | str | None) -> datetime:
    if isinstance(created_at, datetime):
        return created_at
    if isinstance(created_at, str):
        return datetime.fromisoformat(created_at)
    raise HTTPException(status_code=500, detail="Role timestamp is missing")
