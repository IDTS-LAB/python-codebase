from datetime import datetime

from src.modules.authorization.domain.entities.permission import Permission
from src.modules.authorization.domain.entities.role import Role
from src.modules.authorization.domain.permissions import permission_key
from src.modules.authorization.domain.services.authorization_service import (
    AuthorizationService,
)
from src.modules.authorization.infrastructure.repositories.casbin_policy_repository import (
    SQLAlchemyCasbinPolicyRepository,
)
from src.shared.utils.cursor import CursorDirection

CASBIN_MODEL_TEXT = """
[request_definition]
r = sub, perm

[policy_definition]
p = sub, perm

[role_definition]
g = _, _

[policy_effect]
e = some(where (p.eft == allow))

[matchers]
m = g(r.sub, p.sub) && (p.perm == "*" || r.perm == p.perm)
"""


class CasbinAuthorizationService(AuthorizationService):
    def __init__(self, policy_repository: SQLAlchemyCasbinPolicyRepository):
        self._policy_repository = policy_repository

    async def can(self, subject: str, resource: str, action: str) -> bool:
        enforcer = await self._build_enforcer()
        return bool(enforcer.enforce(subject, permission_key(resource, action)))

    async def assign_role(self, subject: str, role: str) -> None:
        await self._policy_repository.assign_role(subject, role)

    async def get_roles_for_subject(self, subject: str) -> list[str]:
        return await self._policy_repository.get_roles_for_subject(subject)

    async def create_role(self, role: Role) -> Role:
        return await self._policy_repository.create_role(role)

    async def update_role(self, role: Role) -> Role | None:
        return await self._policy_repository.update_role(role)

    async def delete_role(self, role_id: int) -> None:
        await self._policy_repository.delete_role(role_id)

    async def get_role(self, role_id: int) -> Role | None:
        return await self._policy_repository.get_role(role_id)

    async def list_roles(self) -> list[Role]:
        return await self._policy_repository.list_roles()

    async def list_roles_cursor(
        self,
        cursor_created_at: datetime | None = None,
        cursor_id: int | None = None,
        limit: int = 10,
        direction: CursorDirection = CursorDirection.DIRECTION_NEXT,
    ) -> tuple[list[Role], bool]:
        return await self._policy_repository.list_roles_cursor(
            cursor_created_at=cursor_created_at,
            cursor_id=cursor_id,
            limit=limit,
            direction=direction,
        )

    async def create_permission(self, permission: Permission) -> Permission:
        return await self._policy_repository.create_permission(permission)

    async def update_permission(self, permission: Permission) -> Permission | None:
        return await self._policy_repository.update_permission(permission)

    async def delete_permission(self, permission_id: int) -> None:
        await self._policy_repository.delete_permission(permission_id)

    async def get_permission(self, permission_id: int) -> Permission | None:
        return await self._policy_repository.get_permission(permission_id)

    async def list_permissions(self) -> list[Permission]:
        return await self._policy_repository.list_permissions()

    async def list_permissions_cursor(
        self,
        cursor_created_at: datetime | None = None,
        cursor_id: int | None = None,
        limit: int = 10,
        direction: CursorDirection = CursorDirection.DIRECTION_NEXT,
    ) -> tuple[list[Permission], bool]:
        return await self._policy_repository.list_permissions_cursor(
            cursor_created_at=cursor_created_at,
            cursor_id=cursor_id,
            limit=limit,
            direction=direction,
        )

    async def assign_permission_to_role(
        self,
        role_id: int,
        permission_id: int,
    ) -> None:
        await self._policy_repository.assign_permission_to_role(role_id, permission_id)

    async def remove_permission_from_role(
        self,
        role_id: int,
        permission_id: int,
    ) -> None:
        await self._policy_repository.remove_permission_from_role(
            role_id,
            permission_id,
        )

    async def _build_enforcer(self):
        try:
            import casbin
            from casbin import persist
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                "Casbin is not installed. Run `poetry install` to install project dependencies."
            ) from exc

        model = casbin.Model()
        model.load_model_from_text(CASBIN_MODEL_TEXT)
        enforcer = casbin.Enforcer(model)
        for policy_line in await self._policy_repository.load_policy_lines():
            persist.load_policy_line(policy_line, enforcer.model)
        enforcer.build_role_links()
        return enforcer
