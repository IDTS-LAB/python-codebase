from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.core.bootstrap.event import register_event_handlers
from src.core.database.postgres.session import engine
from src.core.dependency.rate_limit import close_rate_limiter, init_rate_limiter


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_rate_limiter()
    register_event_handlers()

    yield

    await close_rate_limiter()
    await engine.dispose()
