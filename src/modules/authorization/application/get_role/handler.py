from src.modules.authorization.application.get_role.query import GetRoleQuery
from src.modules.authorization.domain.entities.role import Role
from src.modules.authorization.infrastructure.repositories.casbin_policy_repository import (
    CasbinPolicyRepository,
)


class GetRoleQueryHandler:
    def __init__(self, policy_repo: CasbinPolicyRepository):
        self._policy_repo = policy_repo

    async def execute(self, query: GetRoleQuery) -> Role | None:
        return await self._policy_repo.get_role(query.role_id)
