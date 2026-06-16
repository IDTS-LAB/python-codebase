from abc import ABC, abstractmethod
from uuid import UUID

from src.modules.user.domain.entities.refresh_token import RefreshToken


class RefreshTokenRepository(ABC):
    @abstractmethod
    async def get_by_token_hash(self, token_hash: str) -> RefreshToken | None:
        pass

    @abstractmethod
    async def save(self, refresh_token: RefreshToken) -> RefreshToken:
        pass

    @abstractmethod
    async def revoke_by_user_id(self, user_id: UUID) -> None:
        """Revokes all refresh tokens for a user (e.g., on password change or logout)"""
        pass
