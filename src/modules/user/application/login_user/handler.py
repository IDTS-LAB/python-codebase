import hashlib
from datetime import datetime, timedelta, timezone

from src.core.config.setting import get_settings
from src.core.security.jwt import JWTService
from src.core.security.password import PasswordSerrvice
from src.modules.user.application.login_user.command import LoginUserCommand
from src.modules.user.domain.entities.refresh_token import RefreshToken
from src.modules.user.domain.exceptions.user_exception import UserNotFoundError
from src.modules.user.domain.repositories.refresh_token_repository import (
    RefreshTokenRepository,
)
from src.modules.user.domain.repositories.user_repository import UserRepository
from src.shared.exceptions.credential_exception import InvalidCredentialsError
from src.shared.unit_of_work import UnitOfWork

settings = get_settings()


class LoginUserCommandHandler:
    def __init__(
        self,
        user_repository: UserRepository,
        refresh_token_repository: RefreshTokenRepository,
        unit_of_work: UnitOfWork,
    ):
        self._user_repository = user_repository
        self._refresh_token_repository = refresh_token_repository
        self._unit_of_work = unit_of_work

    async def execute(self, command: LoginUserCommand) -> dict[str, str]:
        user = await self._user_repository.get_by_email(command.username)
        if user is None:
            raise UserNotFoundError

        if not user or not PasswordSerrvice.verify_password(
            command.password, user.password
        ):
            raise InvalidCredentialsError("Incorrect email or password")

        access_token = JWTService.create_access_token(data={"sub": str(user.id)})

        refresh_token_str = JWTService.create_refresh_token(data={"sub": str(user.id)})
        token_hash = hashlib.sha256(refresh_token_str.encode()).hexdigest()
        expires_at = datetime.now(timezone.utc) + timedelta(
            minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES
        )

        async with self._unit_of_work:
            new_rt = RefreshToken.create(
                user_id=user.id, token_hash=token_hash, expires_at=expires_at
            )
            await self._refresh_token_repository.save(new_rt)
            await self._unit_of_work.commit()

        return {
            "access_token": access_token,
            "refresh_token": refresh_token_str,
        }
