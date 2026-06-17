from collections.abc import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.core.config.setting import get_settings
from src.shared.database.unit_of_work import SQLAlchemyUnitOfWork
from src.shared.unit_of_work import UnitOfWork

settings = get_settings()

engine = create_async_engine(settings.DATABASE_URL, echo=False, future=True)
AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
)


async def get_db() -> AsyncGenerator[AsyncSession]:
    async with AsyncSessionLocal() as session:
        yield session


def get_unit_of_work(db: AsyncSession = Depends(get_db)) -> UnitOfWork:
    return SQLAlchemyUnitOfWork(db)
