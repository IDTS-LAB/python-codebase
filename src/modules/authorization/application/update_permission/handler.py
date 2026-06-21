from src.modules.authorization.application.update_permission.command import (
    UpdatePermissionCommand,
)
from src.modules.authorization.domain.entities.permission import Permission
from src.modules.authorization.domain.permissions import permission_key
from src.modules.authorization.domain.repositories.casbin_policy_repository import (
    CasbinPolicyRepository,
)
from src.shared.unit_of_work import UnitOfWork


class UpdatePermissionHandler:
    def __init__(
        self,
        policy_repo: CasbinPolicyRepository,
        unit_of_work: UnitOfWork,
    ):
        self._policy_repo = policy_repo
        self._unit_of_work = unit_of_work

    async def execute(self, command: UpdatePermissionCommand) -> Permission | None:
        existing = await self._policy_repo.get_permission(command.permission_id)
        if existing is None:
            return None

        resource = (
            command.resource if command.resource is not None else existing.resource
        )
        action = command.action if command.action is not None else existing.action
        permission = Permission(
            id=command.permission_id,
            key=permission_key(resource, action),
            resource=resource,
            action=action,
            description=(
                command.description
                if command.description is not None
                else existing.description
            ),
        )
        async with self._unit_of_work:
            updated = await self._policy_repo.update_permission(permission)
            await self._unit_of_work.commit()
            return updated
