import time
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.core.bootstrap.event import register_event_handlers
from src.core.config.setting import get_settings
from src.core.database.postgres.session import engine
from src.core.dependency.rate_limit import close_rate_limiter, init_rate_limiter
from src.core.telemetry.metrics import APP_INFO
from src.core.telemetry.tracing import shutdown_tracing

_startup_time: float = 0.0


def get_uptime() -> float:
    return time.perf_counter() - _startup_time


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _startup_time
    _startup_time = time.perf_counter()

    settings = get_settings()
    APP_INFO.info(
        {
            "name": settings.APP_NAME,
            "version": "1.0.0",
            "environment": settings.APP_ENV,
        }
    )

    await init_rate_limiter()
    register_event_handlers()

    yield

    await close_rate_limiter()
    await engine.dispose()
    shutdown_tracing()
