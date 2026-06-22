from src.modules.authorization.application.create_role.command import CreateRoleCommand
from src.modules.authorization.domain.entities.role import Role
from src.modules.authorization.domain.repositories.casbin_policy_repository import (
    CasbinPolicyRepository,
)
from src.shared.unit_of_work import UnitOfWork


class CreateRoleHandler:
    def __init__(
        self,
        policy_repo: CasbinPolicyRepository,
        unit_of_work: UnitOfWork,
    ):
        self._policy_repo = policy_repo
        self._unit_of_work = unit_of_work

    async def execute(self, command: CreateRoleCommand) -> Role:
        role = Role.create(name=command.name, description=command.description)
        async with self._unit_of_work:
            created = await self._policy_repo.create_role(role)
            await self._unit_of_work.commit()
            return created
