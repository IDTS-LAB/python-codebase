import json
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from uuid import UUID

from src.modules.api_key.domain.entities import ApiKey
from src.modules.api_key.domain.repository import ApiKeyRepository
from src.modules.api_key.infrastructure.models import ApiKeyModel


class SQLAlchemyApiKeyRepository(ApiKeyRepository):
    def __init__(self, session: AsyncSession, tenant_id: UUID | None = None):
        self._session = session
        self._tenant_id = tenant_id

    async def create(self, api_key: ApiKey) -> ApiKey:
        model = ApiKeyModel(
            id=str(api_key.id),
            key_prefix=api_key.key_prefix,
            key_hash=api_key.key_hash,
            name=api_key.name,
            permissions=json.dumps(api_key.permissions),
            expires_at=api_key.expires_at,
            is_active=api_key.is_active,
            tenant_id=self._tenant_id,
        )
        self._session.add(model)
        await self._session.flush()
        return api_key

    async def get_by_id(self, id: UUID) -> ApiKey | None:
        stmt = select(ApiKeyModel).where(ApiKeyModel.id == str(id))
        if self._tenant_id:
            stmt = stmt.where(ApiKeyModel.tenant_id == self._tenant_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_key_hash(self, key_hash: str) -> ApiKey | None:
        stmt = select(ApiKeyModel).where(ApiKeyModel.key_hash == key_hash)
        if self._tenant_id:
            stmt = stmt.where(ApiKeyModel.tenant_id == self._tenant_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def list(self, skip: int = 0, limit: int = 100) -> list[ApiKey]:
        stmt = select(ApiKeyModel).order_by(ApiKeyModel.created_at.desc()).offset(skip).limit(limit)
        if self._tenant_id:
            stmt = stmt.where(ApiKeyModel.tenant_id == self._tenant_id)
        result = await self._session.execute(stmt)
        return [self._to_entity(row) for row in result.scalars()]

    async def count(self) -> int:
        stmt = select(func.count(ApiKeyModel.id))
        if self._tenant_id:
            stmt = stmt.where(ApiKeyModel.tenant_id == self._tenant_id)
        result = await self._session.execute(stmt)
        return result.scalar() or 0

    async def revoke(self, id: UUID) -> None:
        model = await self._session.get(ApiKeyModel, str(id))
        if model:
            model.is_active = False

    async def update_last_used(self, id: UUID) -> None:
        model = await self._session.get(ApiKeyModel, str(id))
        if model:
            model.last_used_at = datetime.now(timezone.utc)

    @staticmethod
    def _to_entity(model: ApiKeyModel) -> ApiKey:
        return ApiKey(
            id=UUID(model.id),
            key_prefix=model.key_prefix,
            key_hash=model.key_hash,
            name=model.name,
            permissions=json.loads(model.permissions),
            expires_at=model.expires_at,
            is_active=model.is_active,
            created_at=model.created_at,
            last_used_at=model.last_used_at,
        )
