from sqlalchemy import select, update

from src.modules.user.domain.entities.refresh_token import RefreshToken
from src.modules.user.domain.repositories.refresh_token_repository import (
    RefreshTokenRepository,
)
from src.modules.user.infrastructure.models.refresh_token_model import (
    UserSessionModel as RefreshTokenModel,
)


class SQLAlchemyRefreshTokenRepository(RefreshTokenRepository):
    def __init__(self, db, tenant_id: int | None = None):
        self.db = db
        self._tenant_id = tenant_id

    async def get_by_token_hash(self, token_hash: str) -> RefreshToken | None:
        stmt = select(RefreshTokenModel).where(
            RefreshTokenModel.refresh_token_hash == token_hash
        )
        if self._tenant_id:
            stmt = stmt.where(RefreshTokenModel.tenant_id == self._tenant_id)
        result = await self.db.execute(stmt)
        model = result.scalar_one_or_none()
        if not model:
            return None
        return RefreshToken(
            id=model.id,
            user_id=model.user_id,
            token_hash=model.refresh_token_hash,
            expires_at=model.expires_at,
            is_revoked=model.is_revoked,
        )

    async def save(self, refresh_token: RefreshToken) -> RefreshToken:
        model = RefreshTokenModel(
            user_id=refresh_token.user_id,
            tenant_id=self._tenant_id,
            refresh_token_hash=refresh_token.token_hash,
            expires_at=refresh_token.expires_at,
            is_revoked=refresh_token.is_revoked,
        )
        self.db.add(model)
        await self.db.flush()
        await self.db.refresh(model)
        return RefreshToken(
            id=model.id,
            user_id=model.user_id,
            token_hash=model.refresh_token_hash,
            expires_at=model.expires_at,
            is_revoked=model.is_revoked,
        )

    async def revoke_by_user_id(self, user_id: int) -> None:
        stmt = (
            update(RefreshTokenModel)
            .where(
                RefreshTokenModel.user_id == user_id,
                RefreshTokenModel.is_revoked.is_(False),
            )
            .values(is_revoked=True)
        )
        if self._tenant_id:
            stmt = stmt.where(RefreshTokenModel.tenant_id == self._tenant_id)
        await self.db.execute(stmt)
        await self.db.flush()
