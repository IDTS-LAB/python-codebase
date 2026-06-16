import hashlib
from datetime import datetime, timedelta, timezone

from src.core.config.setting import settings
from src.core.security.jwt import JWTService
from src.modules.user.application.refresh_token.command import RefreshTokenCommand
from src.modules.user.domain.entities.refresh_token import RefreshToken
from src.modules.user.domain.repositories.refresh_token_repository import (
    RefreshTokenRepository,
)
from src.shared.exceptions.credential_exception import InvalidRefreshTokenError
from src.shared.unit_of_work import UnitOfWork


class RefreshTokenCommandHandler:
    def __init__(
        self,
        refresh_token_repo: RefreshTokenRepository,
        unit_of_work: UnitOfWork,
    ):
        self._refresh_token_repo = refresh_token_repo
        self._unit_of_work = unit_of_work

    def _hash_token(self, token: str) -> str:
        return hashlib.sha256(token.encode()).hexdigest()

    async def execute(self, command: RefreshTokenCommand) -> dict:
        token_hash = self._hash_token(command.token)
        stored_token = await self._refresh_token_repo.get_by_token_hash(token_hash)

        if not stored_token:
            raise InvalidRefreshTokenError("Invalid refresh token")
        if stored_token.is_revoked:
            raise InvalidRefreshTokenError("Refresh token has been revoked")
        if stored_token.expires_at < datetime.now(timezone.utc):
            raise InvalidRefreshTokenError("Refresh token has expired")

        async with self._unit_of_work:
            stored_token.revoke()
            await self._refresh_token_repo.save(stored_token)

            new_access_token = JWTService.create_access_token(
                data={"sub": str(stored_token.user_id)}
            )

            new_refresh_token_str = JWTService.create_refresh_token(
                data={"sub": str(stored_token.user_id)}
            )

            new_token_hash = self._hash_token(new_refresh_token_str)

            expires_at = datetime.now(timezone.utc) + timedelta(
                minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES,
            )

            new_refresh_token_entity = RefreshToken.create(
                user_id=stored_token.user_id,
                token_hash=new_token_hash,
                expires_at=expires_at,
            )

            await self._refresh_token_repo.save(new_refresh_token_entity)
            await self._unit_of_work.commit()

        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token_str,
            "token_type": "bearer",
        }
