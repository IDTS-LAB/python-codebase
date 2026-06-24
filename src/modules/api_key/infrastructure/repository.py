import json
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.api_key.domain.entities import ApiKey
from src.modules.api_key.domain.repository import ApiKeyRepository
from src.modules.api_key.infrastructure.models import ApiKeyModel


class SQLAlchemyApiKeyRepository(ApiKeyRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, api_key: ApiKey) -> ApiKey:
        model = ApiKeyModel(
            id=str(api_key.id),
            key_prefix=api_key.key_prefix,
            key_hash=api_key.key_hash,
            name=api_key.name,
            permissions=json.dumps(api_key.permissions),
            expires_at=api_key.expires_at,
            is_active=api_key.is_active,
        )
        self._session.add(model)
        await self._session.flush()
        return api_key

    async def get_by_id(self, id: UUID) -> ApiKey | None:
        result = await self._session.execute(
            select(ApiKeyModel).where(ApiKeyModel.id == str(id))
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_key_hash(self, key_hash: str) -> ApiKey | None:
        result = await self._session.execute(
            select(ApiKeyModel).where(ApiKeyModel.key_hash == key_hash)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def list(self, skip: int = 0, limit: int = 100) -> list[ApiKey]:
        result = await self._session.execute(
            select(ApiKeyModel)
            .order_by(ApiKeyModel.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return [self._to_entity(row) for row in result.scalars()]

    async def count(self) -> int:
        result = await self._session.execute(
            select(func.count(ApiKeyModel.id))
        )
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
