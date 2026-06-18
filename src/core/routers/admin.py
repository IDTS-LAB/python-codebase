from fastapi import APIRouter, FastAPI, status
from fastapi.responses import JSONResponse

from src.core.database.postgres.session import engine
from src.core.database.redis.client import get_redis_client

router = APIRouter()


@router.get("/live", include_in_schema=False)
async def live():
    return {"status": "alive"}


@router.get("/ready", include_in_schema=False)
async def ready():
    checks = {"database": "ok", "redis": "ok"}
    http_status = status.HTTP_200_OK

    try:
        async with engine.connect() as connection:
            await connection.exec_driver_sql("SELECT 1")
    except Exception:
        checks["database"] = "unavailable"
        http_status = status.HTTP_503_SERVICE_UNAVAILABLE

    try:
        redis = await get_redis_client()
        await redis.ping()
    except Exception:
        checks["redis"] = "unavailable"
        http_status = status.HTTP_503_SERVICE_UNAVAILABLE

    return JSONResponse(
        status_code=http_status,
        content={
            "status": "ready" if http_status == status.HTTP_200_OK else "not_ready",
            "checks": checks,
        },
    )


def register_router(app: FastAPI):
    app.include_router(router)
