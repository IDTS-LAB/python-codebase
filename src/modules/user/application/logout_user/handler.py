from src.modules.user.application.logout_user.command import LogoutUserCommand
from src.modules.user.application.logout_user.validation import (
    validate_logout_user_command,
)
from src.modules.user.domain.repositories.refresh_token_repository import (
    RefreshTokenRepository,
)
from src.shared.unit_of_work import UnitOfWork


class LogoutUserCommandHandler:
    def __init__(
        self, refresh_token_repository: RefreshTokenRepository, unit_of_work: UnitOfWork
    ):
        self._refresh_token_repository = refresh_token_repository
        self._unit_of_work = unit_of_work

    async def excute(self, command: LogoutUserCommand) -> None:
        validate_logout_user_command(command)

        async with self._unit_of_work:
            self._refresh_token_repository.revoke_by_user_id(command.user_id)
            await self._unit_of_work.commit()
