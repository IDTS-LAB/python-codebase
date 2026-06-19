import pytest

from src.core.authorization.permissions import (
    ADMIN_ROLE,
    DEFAULT_RESOURCES,
    DEFAULT_ROLES,
    DEFAULT_POLICIES,
    DEFAULT_USER_ROLE,
    MANAGER_ROLE,
    VIEWER_ROLE,
)
from src.core.seed.authorization import seed_authorization
from src.modules.authorization.domain.entities.permission import Permission
from src.modules.authorization.domain.entities.resource import AuthorizationResource
from src.modules.authorization.domain.entities.role import Role


class FakePolicyRepository:
    def __init__(self):
        self.resources: dict[str, AuthorizationResource] = {}
        self.roles: dict[str, Role] = {}
        self.permissions: dict[str, Permission] = {}
        self.role_permissions: set[tuple[str, str]] = set()
        self.policies: set[tuple[str, str, str]] = set()

    async def list_resources(self) -> list[AuthorizationResource]:
        return list(self.resources.values())

    async def create_resource(
        self,
        resource: AuthorizationResource,
    ) -> AuthorizationResource:
        self.resources[resource.key] = resource
        return resource

    async def list_roles(self) -> list[Role]:
        return list(self.roles.values())

    async def create_role(self, role: Role) -> Role:
        self.roles[role.name] = role
        return role

    async def list_permissions(self) -> list[Permission]:
        return list(self.permissions.values())

    async def create_permission(self, permission: Permission) -> Permission:
        self.permissions[permission.key] = permission
        return permission

    async def list_role_permissions(self) -> list[tuple[str, str]]:
        return list(self.role_permissions)

    async def assign_permission_to_role(
        self,
        role_id,
        permission_id,
    ) -> None:
        role = next(role for role in self.roles.values() if role.id == role_id)
        permission = next(
            permission
            for permission in self.permissions.values()
            if permission.id == permission_id
        )
        self.role_permissions.add((role.name, permission.key))

    async def add_policy(self, ptype: str, *values: str) -> None:
        self.policies.add((ptype, *values))

    async def list_policies(self) -> list[tuple[str, ...]]:
        return list(self.policies)


@pytest.mark.anyio
async def test_seed_authorization_creates_default_roles_permissions_and_policies():
    repository = FakePolicyRepository()

    result = await seed_authorization(repository)

    assert {resource.key for resource in DEFAULT_RESOURCES}.issubset(
        repository.resources.keys()
    )
    assert {
        ADMIN_ROLE,
        DEFAULT_USER_ROLE,
        MANAGER_ROLE,
        VIEWER_ROLE,
    }.issubset(repository.roles.keys())
    assert {
        policy[2]
        for policy in DEFAULT_POLICIES
        if policy[0] == "p" and policy[2] != "*"
    }.issubset(repository.permissions.keys())
    assert ("p", ADMIN_ROLE, "*") in repository.policies
    assert ("p", DEFAULT_USER_ROLE, "todo:create") in repository.policies
    assert ("p", MANAGER_ROLE, "todo:update") in repository.policies
    assert ("p", VIEWER_ROLE, "todo:read") in repository.policies
    assert (DEFAULT_USER_ROLE, "todo:create") in repository.role_permissions
    assert (MANAGER_ROLE, "todo:update") in repository.role_permissions
    assert (VIEWER_ROLE, "todo:read") in repository.role_permissions
    assert result.resources_created == len(DEFAULT_RESOURCES)
    assert result.roles_created == len(DEFAULT_ROLES)
    assert result.permissions_created == 5
    assert result.role_permissions_created == len(
        [policy for policy in DEFAULT_POLICIES if policy[0] == "p" and policy[2] != "*"]
    )
    assert result.policies_created == len(DEFAULT_POLICIES)


@pytest.mark.anyio
async def test_seed_authorization_is_idempotent():
    repository = FakePolicyRepository()

    await seed_authorization(repository)
    result = await seed_authorization(repository)

    assert result.roles_created == 0
    assert result.resources_created == 0
    assert result.permissions_created == 0
    assert result.role_permissions_created == 0
    assert result.policies_created == 0
    assert len(repository.resources) == len(DEFAULT_RESOURCES)
    assert len(repository.roles) == len(DEFAULT_ROLES)
    assert len(repository.permissions) == 5
    assert len(repository.role_permissions) == len(
        [policy for policy in DEFAULT_POLICIES if policy[0] == "p" and policy[2] != "*"]
    )
    assert len(repository.policies) == len(DEFAULT_POLICIES)
