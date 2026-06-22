from src.modules.authorization.application.create_permission.command import (
    CreatePermissionCommand,
)
from src.modules.authorization.domain.entities.permission import Permission
from src.modules.authorization.domain.permissions import permission_key
from src.modules.authorization.domain.repositories.casbin_policy_repository import (
    CasbinPolicyRepository,
)
from src.shared.unit_of_work import UnitOfWork


class CreatePermissionHandler:
    def __init__(
        self,
        policy_repo: CasbinPolicyRepository,
        unit_of_work: UnitOfWork,
    ):
        self._policy_repo = policy_repo
        self._unit_of_work = unit_of_work

    async def execute(self, command: CreatePermissionCommand) -> Permission:
        permission = Permission.create(
            key=permission_key(command.resource, command.action),
            resource=command.resource,
            action=command.action,
            description=command.description,
        )
        async with self._unit_of_work:
            created = await self._policy_repo.create_permission(permission)
            await self._unit_of_work.commit()
            return created
