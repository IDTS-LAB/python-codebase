from src.modules.authorization.application.delete_permission.command import (
    DeletePermissionCommand,
)
from src.modules.authorization.domain.repositories.casbin_policy_repository import (
    CasbinPolicyRepository,
)
from src.shared.unit_of_work import UnitOfWork


class DeletePermissionHandler:
    def __init__(
        self,
        policy_repo: CasbinPolicyRepository,
        unit_of_work: UnitOfWork,
    ):
        self._policy_repo = policy_repo
        self._unit_of_work = unit_of_work

    async def execute(self, command: DeletePermissionCommand) -> None:
        async with self._unit_of_work:
            await self._policy_repo.delete_permission(command.permission_id)
            await self._unit_of_work.commit()
