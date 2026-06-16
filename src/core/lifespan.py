from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.shared.database.model import Base
from src.core.database.session import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create database tables (Use Alembic in real production)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown: Dispose engine
    await engine.dispose()
