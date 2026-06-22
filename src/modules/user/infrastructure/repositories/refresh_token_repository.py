from uuid import UUID

from sqlalchemy import select, update

from src.modules.user.domain.entities.refresh_token import RefreshToken
from src.modules.user.domain.repositories.refresh_token_repository import (
    RefreshTokenRepository,
)
from src.modules.user.infrastructure.models.refresh_token_model import (
    UserSessionModel as RefreshTokenModel,
)


class SQLAlchemyRefreshTokenRepository(RefreshTokenRepository):
    def __init__(self, db):
        self.db = db

    async def get_by_token_hash(self, token_hash: str) -> RefreshToken | None:
        result = await self.db.execute(
            select(RefreshTokenModel).where(RefreshTokenModel.token_hash == token_hash)
        )
        model = result.scalar_one_or_none()
        if not model:
            return None
        return RefreshToken(
            id=model.id,
            user_id=model.user_id,
            token_hash=model.token_hash,
            expires_at=model.expires_at,
            is_revoked=model.is_revoked,
        )

    async def save(self, refresh_token: RefreshToken) -> RefreshToken:
        model = RefreshTokenModel(
            id=refresh_token.id,
            user_id=refresh_token.user_id,
            token_hash=refresh_token.token_hash,
            expires_at=refresh_token.expires_at,
            is_revoked=refresh_token.is_revoked,
        )
        model = await self.db.merge(model)
        await self.db.flush()
        await self.db.refresh(model)
        return RefreshToken(
            id=model.id,
            user_id=model.user_id,
            token_hash=model.token_hash,
            expires_at=model.expires_at,
            is_revoked=model.is_revoked,
        )

    async def revoke_by_user_id(self, user_id: UUID) -> None:
        await self.db.execute(
            update(RefreshTokenModel)
            .where(
                RefreshTokenModel.user_id == user_id,
                RefreshTokenModel.is_revoked.is_(False),
            )
            .values(is_revoked=True)
        )
        await self.db.flush()
