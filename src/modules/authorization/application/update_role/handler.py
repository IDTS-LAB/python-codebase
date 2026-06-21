from src.modules.authorization.application.update_role.command import UpdateRoleCommand
from src.modules.authorization.domain.entities.role import Role
from src.modules.authorization.domain.repositories.casbin_policy_repository import (
    CasbinPolicyRepository,
)
from src.shared.unit_of_work import UnitOfWork


class UpdateRoleHandler:
    def __init__(
        self,
        policy_repo: CasbinPolicyRepository,
        unit_of_work: UnitOfWork,
    ):
        self._policy_repo = policy_repo
        self._unit_of_work = unit_of_work

    async def execute(self, command: UpdateRoleCommand) -> Role | None:
        existing = await self._policy_repo.get_role(command.role_id)
        if existing is None:
            return None

        role = Role(
            id=command.role_id,
            name=command.name if command.name is not None else existing.name,
            description=(
                command.description
                if command.description is not None
                else existing.description
            ),
        )
        async with self._unit_of_work:
            updated = await self._policy_repo.update_role(role)
            await self._unit_of_work.commit()
            return updated
