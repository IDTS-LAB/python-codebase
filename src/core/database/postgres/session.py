from collections.abc import AsyncGenerator
from uuid import UUID

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.core.config.setting import get_settings
from src.core.database.unit_of_work import SQLAlchemyUnitOfWork
from src.core.dependency.tenant import get_optional_tenant_id
from src.shared.unit_of_work import UnitOfWork

settings = get_settings()

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_pre_ping=True,
    pool_timeout=settings.DATABASE_POOL_TIMEOUT,
    pool_recycle=settings.DATABASE_POOL_RECYCLE,
)
AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
)


async def get_db() -> AsyncGenerator[AsyncSession]:
    async with AsyncSessionLocal() as session:
        yield session


def get_unit_of_work(
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID | None = Depends(get_optional_tenant_id),
) -> UnitOfWork:
    return SQLAlchemyUnitOfWork(db, tenant_id)
