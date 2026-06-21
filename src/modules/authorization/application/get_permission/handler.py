from src.modules.authorization.application.get_permission.query import GetPermissionQuery
from src.modules.authorization.domain.entities.permission import Permission
from src.modules.authorization.domain.repositories.casbin_policy_repository import (
    CasbinPolicyRepository,
)


class GetPermissionQueryHandler:
    def __init__(self, policy_repo: CasbinPolicyRepository):
        self._policy_repo = policy_repo

    async def execute(self, query: GetPermissionQuery) -> Permission | None:
        return await self._policy_repo.get_permission(query.permission_id)
