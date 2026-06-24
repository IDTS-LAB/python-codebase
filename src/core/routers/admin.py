from fastapi import APIRouter, FastAPI, status
from fastapi.responses import JSONResponse, PlainTextResponse
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from src.core.database.postgres.session import engine
from src.core.database.redis.client import get_redis_client
from src.core.lifespan import get_uptime

router = APIRouter()


def _get_app_version() -> str:
    return "1.0.0"


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


@router.get("/health", tags=["Health Check"])
async def health():
    overall_status = "pass"
    checks = {}

    try:
        async with engine.connect() as connection:
            await connection.exec_driver_sql("SELECT 1")
        checks["database"] = {
            "status": "pass",
            "componentType": "datastore",
            "observedValue": "connected",
            "observedUnit": "status",
        }
    except Exception:
        checks["database"] = {
            "status": "fail",
            "componentType": "datastore",
            "observedValue": "disconnected",
            "observedUnit": "status",
        }
        overall_status = "fail"

    try:
        redis = await get_redis_client()
        await redis.ping()
        checks["redis"] = {
            "status": "pass",
            "componentType": "datastore",
            "observedValue": "connected",
            "observedUnit": "status",
        }
    except Exception:
        checks["redis"] = {
            "status": "fail",
            "componentType": "datastore",
            "observedValue": "disconnected",
            "observedUnit": "status",
        }
        overall_status = "fail"

    http_status = (
        status.HTTP_200_OK
        if overall_status == "pass"
        else status.HTTP_503_SERVICE_UNAVAILABLE
    )

    return JSONResponse(
        status_code=http_status,
        content={
            "status": overall_status,
            "version": _get_app_version(),
            "releaseId": _get_app_version(),
            "uptime": round(get_uptime(), 2),
            "checks": checks,
        },
    )


@router.get("/metrics", include_in_schema=False)
async def metrics():
    return PlainTextResponse(
        content=generate_latest().decode("utf-8"),
        media_type=CONTENT_TYPE_LATEST,
    )


def register_router(app: FastAPI):
    app.include_router(router)
