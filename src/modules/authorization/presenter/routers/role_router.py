from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from src.core.authorization.infrastructure.services.casbin_authorization_service import (
    CasbinAuthorizationService,
)
from src.core.database.postgres.session import get_unit_of_work
from src.modules.authorization.domain.entities.role import Role
from src.modules.authorization.presenter.dependency import (
    get_casbin_authorization_service,
)
from src.modules.authorization.presenter.schema.request import (
    CreateRoleRequest,
    UpdateRoleRequest,
)
from src.shared.unit_of_work import UnitOfWork

router = APIRouter(prefix="/roles", tags=["Role"])


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_role(
    request: CreateRoleRequest,
    service: CasbinAuthorizationService = Depends(get_casbin_authorization_service),
    unit_of_work: UnitOfWork = Depends(get_unit_of_work),
):
    role = Role.create(name=request.name, description=request.description)
    async with unit_of_work:
        created = await service.create_role(role)
        await unit_of_work.commit()
    return _role_response(created)


@router.get("/")
async def list_roles(
    service: CasbinAuthorizationService = Depends(get_casbin_authorization_service),
):
    return [_role_response(role) for role in await service.list_roles()]


@router.get("/{role_id}")
async def get_role(
    role_id: UUID,
    service: CasbinAuthorizationService = Depends(get_casbin_authorization_service),
):
    role = await service.get_role(role_id)
    if role is None:
        raise HTTPException(status_code=404, detail="Role not found")
    return _role_response(role)


@router.patch("/{role_id}")
async def update_role(
    role_id: UUID,
    request: UpdateRoleRequest,
    service: CasbinAuthorizationService = Depends(get_casbin_authorization_service),
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
    return _role_response(updated)


@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role(
    role_id: UUID,
    service: CasbinAuthorizationService = Depends(get_casbin_authorization_service),
    unit_of_work: UnitOfWork = Depends(get_unit_of_work),
):
    async with unit_of_work:
        await service.delete_role(role_id)
        await unit_of_work.commit()


@router.post(
    "/{role_id}/permissions/{permission_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def assign_permission_to_role(
    role_id: UUID,
    permission_id: UUID,
    service: CasbinAuthorizationService = Depends(get_casbin_authorization_service),
    unit_of_work: UnitOfWork = Depends(get_unit_of_work),
):
    async with unit_of_work:
        await service.assign_permission_to_role(role_id, permission_id)
        await unit_of_work.commit()


@router.delete(
    "/{role_id}/permissions/{permission_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_permission_from_role(
    role_id: UUID,
    permission_id: UUID,
    service: CasbinAuthorizationService = Depends(get_casbin_authorization_service),
    unit_of_work: UnitOfWork = Depends(get_unit_of_work),
):
    async with unit_of_work:
        await service.remove_permission_from_role(role_id, permission_id)
        await unit_of_work.commit()


def _role_response(role: Role | None) -> dict:
    if role is None:
        raise HTTPException(status_code=404, detail="Role not found")
    return {
        "id": str(role.id),
        "name": role.name,
        "description": role.description,
    }
