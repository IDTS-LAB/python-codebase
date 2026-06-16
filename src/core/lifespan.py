from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.core.database.session import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create database tables (Use Alembic in real production)
    yield

    # Shutdown: Dispose engine
    await engine.dispose()
