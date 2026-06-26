from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database.postgres.session import get_db
from src.modules.tenants.domain.repositories.tenant_repository import TenantRepository
from src.modules.tenants.infrastructure.repositories.tenant_repository import (
    SQLAlchemyTenantRepository,
)


def get_tenant_repository(
    db: AsyncSession = Depends(get_db),
) -> TenantRepository:
    return SQLAlchemyTenantRepository(db)
