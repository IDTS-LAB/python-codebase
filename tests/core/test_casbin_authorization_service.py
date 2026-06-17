import asyncio

from src.core.authorization.infrastructure.services.casbin_authorization_service import (
    CasbinAuthorizationService,
)
from src.core.authorization.permissions import DEFAULT_POLICIES


class FakePolicyRepository:
    def __init__(self):
        self.policies = [", ".join(policy) for policy in DEFAULT_POLICIES]
        self.user_roles = {}

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
