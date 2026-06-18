from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from src.core.authorization.dependencies import require_permission
from src.core.authorization.infrastructure.services.casbin_authorization_service import (
    CasbinAuthorizationService,
)
from src.core.authorization.permissions import (
    CREATE_ACTION,
    DELETE_ACTION,
    PERMISSION_RESOURCE,
    READ_ACTION,
    UPDATE_ACTION,
    permission_key,
)
from src.core.database.postgres.session import get_unit_of_work
from src.core.schemas.response import PaginatedResponse, SuccessResponse
from src.modules.authorization.domain.entities.permission import Permission
from src.modules.authorization.presenter.dependency import (
    get_casbin_authorization_service,
)
from src.modules.authorization.presenter.schema.request import (
    CreatePermissionRequest,
    UpdatePermissionRequest,
)
from src.modules.authorization.presenter.schema.response import PermissionResponse
from src.shared.unit_of_work import UnitOfWork

router = APIRouter(prefix="/permissions", tags=["Permission"])


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=SuccessResponse[PermissionResponse],
    dependencies=[Depends(require_permission(PERMISSION_RESOURCE, CREATE_ACTION))],
)
async def create_permission(
    request: CreatePermissionRequest,
    service: CasbinAuthorizationService = Depends(get_casbin_authorization_service),
    unit_of_work: UnitOfWork = Depends(get_unit_of_work),
):
    permission = Permission.create(
        key=permission_key(request.resource, request.action),
        resource=request.resource,
        action=request.action,
        description=request.description,
    )
    async with unit_of_work:
        created = await service.create_permission(permission)
        await unit_of_work.commit()

    return SuccessResponse(
        success=True,
        message="create permission success",
        data=_permission_response(created),
    )


@router.get(
    "/",
    response_model=PaginatedResponse[PermissionResponse],
    dependencies=[Depends(require_permission(PERMISSION_RESOURCE, READ_ACTION))],
)
async def list_permissions(
    service: CasbinAuthorizationService = Depends(get_casbin_authorization_service),
):
    return PaginatedResponse(
        success=True,
        message="fetch permission success",
        data=[
            _permission_response(permission)
            for permission in await service.list_permissions()
        ],
    )


@router.get(
    "/{permission_id}",
    response_model=SuccessResponse[PermissionResponse],
    dependencies=[Depends(require_permission(PERMISSION_RESOURCE, READ_ACTION))],
)
async def get_permission(
    permission_id: UUID,
    service: CasbinAuthorizationService = Depends(get_casbin_authorization_service),
):
    permission = await service.get_permission(permission_id)
    if permission is None:
        raise HTTPException(status_code=404, detail="Permission not found")
    return SuccessResponse(
        success=True,
        message="fetch permission success",
        data=_permission_response(permission),
    )


@router.patch(
    "/{permission_id}",
    response_model=SuccessResponse[PermissionResponse],
    dependencies=[Depends(require_permission(PERMISSION_RESOURCE, UPDATE_ACTION))],
)
async def update_permission(
    permission_id: UUID,
    request: UpdatePermissionRequest,
    service: CasbinAuthorizationService = Depends(get_casbin_authorization_service),
    unit_of_work: UnitOfWork = Depends(get_unit_of_work),
):
    existing = await service.get_permission(permission_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="Permission not found")

    resource = request.resource if request.resource is not None else existing.resource
    action = request.action if request.action is not None else existing.action
    permission = Permission(
        id=permission_id,
        key=permission_key(resource, action),
        resource=resource,
        action=action,
        description=(
            request.description
            if request.description is not None
            else existing.description
        ),
    )
    async with unit_of_work:
        updated = await service.update_permission(permission)
        await unit_of_work.commit()

    return SuccessResponse(
        success=True,
        message="update permission success",
        data=_permission_response(updated),
    )


@router.delete(
    "/{permission_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission(PERMISSION_RESOURCE, DELETE_ACTION))],
)
async def delete_permission(
    permission_id: UUID,
    service: CasbinAuthorizationService = Depends(get_casbin_authorization_service),
    unit_of_work: UnitOfWork = Depends(get_unit_of_work),
):
    async with unit_of_work:
        await service.delete_permission(permission_id)
        await unit_of_work.commit()


def _permission_response(permission: Permission | None) -> PermissionResponse:
    if permission is None:
        raise HTTPException(status_code=404, detail="Permission not found")
    return PermissionResponse(
        id=str(permission.id),
        key=permission.key,
        resource=permission.resource,
        action=permission.action,
        description=permission.description,
    )
