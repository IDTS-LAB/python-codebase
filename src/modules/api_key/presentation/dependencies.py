from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database.postgres.session import get_db
from src.modules.api_key.application.service import ApiKeyService
from src.modules.api_key.domain.repository import ApiKeyRepository
from src.modules.api_key.infrastructure.repository import (
    SQLAlchemyApiKeyRepository,
)


async def get_api_key_repository(
    db: AsyncSession = Depends(get_db),
) -> ApiKeyRepository:
    return SQLAlchemyApiKeyRepository(db)


async def get_api_key_service(
    repo: ApiKeyRepository = Depends(get_api_key_repository),
) -> ApiKeyService:
    return ApiKeyService(repo)
