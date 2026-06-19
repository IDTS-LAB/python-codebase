from dataclasses import dataclass
from typing import Protocol

from src.core.authorization.permissions import (
    ADMIN_ROLE,
    DEFAULT_RESOURCES,
    DEFAULT_POLICIES,
    DEFAULT_USER_ROLE,
)
from src.modules.authorization.domain.entities.permission import Permission
from src.modules.authorization.domain.entities.resource import AuthorizationResource
from src.modules.authorization.domain.entities.role import Role


class AuthorizationSeedRepository(Protocol):
    async def list_resources(self) -> list[AuthorizationResource]:
        raise NotImplementedError

    async def create_resource(
        self,
        resource: AuthorizationResource,
    ) -> AuthorizationResource:
        raise NotImplementedError

    async def list_roles(self) -> list[Role]:
        raise NotImplementedError

    async def create_role(self, role: Role) -> Role:
        raise NotImplementedError

    async def list_permissions(self) -> list[Permission]:
        raise NotImplementedError

    async def create_permission(self, permission: Permission) -> Permission:
        raise NotImplementedError

    async def assign_permission_to_role(
        self,
        role_id,
        permission_id,
    ) -> None:
        raise NotImplementedError

    async def add_policy(self, ptype: str, *values: str) -> None:
        raise NotImplementedError


@dataclass(frozen=True)
class AuthorizationSeedResult:
    resources_created: int = 0
    roles_created: int = 0
    permissions_created: int = 0
    role_permissions_created: int = 0
    policies_created: int = 0


async def seed_authorization(
    repository: AuthorizationSeedRepository,
) -> AuthorizationSeedResult:
    existing_resources = {
        resource.key: resource for resource in await repository.list_resources()
    }
    existing_roles = {role.name: role for role in await repository.list_roles()}
    existing_permissions = {
        permission.key: permission for permission in await repository.list_permissions()
    }
    existing_role_permissions = await _load_role_permissions(repository)
    existing_policies = await _load_policies(repository)

    resources_created = 0
    for resource_definition in DEFAULT_RESOURCES:
        if resource_definition.key in existing_resources:
            continue

        resource = await repository.create_resource(
            AuthorizationResource.create(
                key=resource_definition.key,
                name=resource_definition.name,
                description=resource_definition.description,
            )
        )
        existing_resources[resource.key] = resource
        resources_created += 1

    roles_created = 0
    for name, description in _default_roles().items():
        if name in existing_roles:
            continue

        role = await repository.create_role(Role.create(name=name, description=description))
        existing_roles[role.name] = role
        roles_created += 1

    permissions_created = 0
    for key in _default_permission_keys():
        if key in existing_permissions:
            continue

        resource, action = key.split(":", 1)
        permission = await repository.create_permission(
            Permission.create(
                key=key,
                resource=resource,
                action=action,
                description=f"Allows {action} access on {resource}",
            )
        )
        existing_permissions[permission.key] = permission
        permissions_created += 1

    role_permissions_created = 0
    for _, role_name, permission_key in _permission_policies():
        role_permission = (role_name, permission_key)
        if role_permission in existing_role_permissions:
            continue

        await repository.assign_permission_to_role(
            existing_roles[role_name].id,
            existing_permissions[permission_key].id,
        )
        existing_role_permissions.add(role_permission)
        role_permissions_created += 1

    policies_created = 0
    for policy in DEFAULT_POLICIES:
        if policy in existing_policies:
            continue

        ptype, *values = policy
        await repository.add_policy(ptype, *values)
        existing_policies.add(policy)
        policies_created += 1

    return AuthorizationSeedResult(
        resources_created=resources_created,
        roles_created=roles_created,
        permissions_created=permissions_created,
        role_permissions_created=role_permissions_created,
        policies_created=policies_created,
    )


def _default_roles() -> dict[str, str]:
    return {
        ADMIN_ROLE: "Administrator with full platform access",
        DEFAULT_USER_ROLE: "Default authenticated user",
    }


def _default_permission_keys() -> list[str]:
    return [
        permission_key
        for _, _, permission_key in _permission_policies()
    ]


def _permission_policies() -> list[tuple[str, str, str]]:
    return [
        policy
        for policy in DEFAULT_POLICIES
        if policy[0] == "p" and policy[2] != "*"
    ]


async def _load_role_permissions(
    repository: AuthorizationSeedRepository,
) -> set[tuple[str, str]]:
    if not hasattr(repository, "list_role_permissions"):
        return set()

    return set(await repository.list_role_permissions())


async def _load_policies(
    repository: AuthorizationSeedRepository,
) -> set[tuple[str, ...]]:
    if not hasattr(repository, "list_policies"):
        return set()

    return set(await repository.list_policies())
