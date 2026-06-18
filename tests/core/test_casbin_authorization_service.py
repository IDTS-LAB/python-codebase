import asyncio
from uuid import uuid4

from src.core.authorization.infrastructure.services.casbin_authorization_service import (
    CasbinAuthorizationService,
)
from src.core.authorization.permissions import DEFAULT_POLICIES
from src.modules.authorization.domain.entities.permission import Permission
from src.modules.authorization.domain.entities.role import Role


class FakePolicyRepository:
    def __init__(self):
        self.policies = [", ".join(policy) for policy in DEFAULT_POLICIES]
        self.user_roles = {}
        self.roles = {}
        self.permissions = {}
        self.assigned_permissions = []

    async def load_policy_lines(self) -> list[str]:
        return self.policies

    async def add_policy(self, ptype: str, *values: str) -> None:
        policy = ", ".join([ptype, *values])
        if policy not in self.policies:
            self.policies.append(policy)

    async def assign_role(self, subject: str, role: str) -> None:
        self.user_roles.setdefault(subject, [])
        if role not in self.user_roles[subject]:
            self.user_roles[subject].append(role)
        await self.add_policy("g", subject, role)

    async def get_roles_for_subject(self, subject: str) -> list[str]:
        return self.user_roles.get(subject, [])

    async def create_role(self, role: Role) -> Role:
        self.roles[role.id] = role
        return role

    async def get_role(self, role_id):
        return self.roles.get(role_id)

    async def list_roles(self):
        return list(self.roles.values())

    async def update_role(self, role: Role):
        self.roles[role.id] = role
        return role

    async def delete_role(self, role_id) -> None:
        self.roles.pop(role_id, None)

    async def create_permission(self, permission: Permission) -> Permission:
        self.permissions[permission.id] = permission
        return permission

    async def get_permission(self, permission_id):
        return self.permissions.get(permission_id)

    async def list_permissions(self):
        return list(self.permissions.values())

    async def update_permission(self, permission: Permission):
        self.permissions[permission.id] = permission
        return permission

    async def delete_permission(self, permission_id) -> None:
        self.permissions.pop(permission_id, None)

    async def assign_permission_to_role(self, role_id, permission_id) -> None:
        self.assigned_permissions.append((role_id, permission_id))
        role = self.roles[role_id]
        permission = self.permissions[permission_id]
        await self.add_policy("p", role.name, permission.key)

    async def remove_permission_from_role(self, role_id, permission_id) -> None:
        self.assigned_permissions.remove((role_id, permission_id))


def test_casbin_authorization_service_enforces_database_policies():
    async def run():
        repository = FakePolicyRepository()
        service = CasbinAuthorizationService(repository)

        assert await service.can("user-1", "todo", "create") is False

        await service.assign_role("user-1", "user")

        assert await service.can("user-1", "todo", "create") is True
        assert await service.can("user-1", "admin", "delete") is False
        assert await service.get_roles_for_subject("user-1") == ["user"]

    asyncio.run(run())


def test_default_policies_use_normalized_permission_keys():
    policy_lines = [", ".join(policy) for policy in DEFAULT_POLICIES]

    assert "p, user, todo:create" in policy_lines
    assert "p, user, user:me" in policy_lines
    assert "p, user, todo, create" not in policy_lines


def test_authorization_service_manages_roles_permissions_and_assignments():
    async def run():
        repository = FakePolicyRepository()
        service = CasbinAuthorizationService(repository)
        role = Role(id=uuid4(), name="manager", description="Manager")
        permission = Permission(
            id=uuid4(),
            key="todo:review",
            resource="todo",
            action="review",
            description="Review todos",
        )

        await service.create_role(role)
        await service.create_permission(permission)
        await service.assign_permission_to_role(role.id, permission.id)

        assert await service.get_role(role.id) == role
        assert await service.list_roles() == [role]
        assert await service.get_permission(permission.id) == permission
        assert await service.list_permissions() == [permission]
        assert await service.can("user-1", "todo", "review") is False

        await service.assign_role("user-1", "manager")

        assert await service.can("user-1", "todo", "review") is True

        updated_role = Role(id=role.id, name="manager", description="Updated")
        updated_permission = Permission(
            id=permission.id,
            key="todo:approve",
            resource="todo",
            action="approve",
            description="Approve todos",
        )
        assert await service.update_role(updated_role) == updated_role
        assert await service.update_permission(updated_permission) == updated_permission

        await service.remove_permission_from_role(role.id, permission.id)
        await service.delete_permission(permission.id)
        await service.delete_role(role.id)

        assert await service.get_role(role.id) is None
        assert await service.get_permission(permission.id) is None

    asyncio.run(run())
