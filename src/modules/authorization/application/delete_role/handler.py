from src.modules.authorization.application.delete_role.command import DeleteRoleCommand
from src.modules.authorization.domain.repositories.casbin_policy_repository import (
    CasbinPolicyRepository,
)
from src.shared.unit_of_work import UnitOfWork


class DeleteRoleHandler:
    def __init__(
        self,
        policy_repo: CasbinPolicyRepository,
        unit_of_work: UnitOfWork,
    ):
        self._policy_repo = policy_repo
        self._unit_of_work = unit_of_work

    async def execute(self, command: DeleteRoleCommand) -> None:
        async with self._unit_of_work:
            await self._policy_repo.delete_role(command.role_id)
            await self._unit_of_work.commit()
