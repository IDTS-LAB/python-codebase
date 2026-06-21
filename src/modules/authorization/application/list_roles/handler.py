from src.modules.authorization.application.list_roles.query import ListRolesQuery
from src.modules.authorization.domain.entities.role import Role
from src.modules.authorization.domain.repositories.casbin_policy_repository import (
    CasbinPolicyRepository,
)


class ListRolesQueryHandler:
    def __init__(self, policy_repo: CasbinPolicyRepository):
        self._policy_repo = policy_repo

    async def execute(self, query: ListRolesQuery) -> list[Role]:
        return await self._policy_repo.list_roles()
