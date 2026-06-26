from fastapi import Depends, FastAPI

import src.core.routers.admin as admin_router
import src.core.routers.api.v1 as v1_router
import src.core.routers.telemetry as web_router
from src.core import lifespan
from src.core.bootstrap.exception import register_exception
from src.core.bootstrap.middleware import register_middleware
from src.core.config.setting import get_settings
from src.core.database.postgres.session import engine
from src.core.dependency.rate_limit import apply_global_rate_limit
from src.core.middleware.structured_logging import configure_logging
from src.core.telemetry.tracing import instrument_app, setup_tracing

settings = get_settings()


def create_app(app_settings=settings) -> FastAPI:
    configure_logging(app_settings.LOG_FORMAT)

    app = FastAPI(
        title=app_settings.APP_NAME,
        version="1.0.0",
        lifespan=lifespan.lifespan,
        docs_url=None if app_settings.is_production else "/docs",
        redoc_url=None if app_settings.is_production else "/redoc",
        openapi_url=None if app_settings.is_production else "/openapi.json",
        swagger_ui_parameters={
            "persistAuthorization": True,
            "displayRequestDuration": True,
            "filter": True,
            "deepLinking": True,
            "tryItOutEnabled": True,
        },
        dependencies=[Depends(apply_global_rate_limit)],
    )

    register_exception(app=app)
    register_middleware(app=app)
    v1_router.register_router(app=app)
    admin_router.register_router(app=app)
    web_router.register_router(app=app)

    setup_tracing(app_settings)
    instrument_app(app=app, db_engine=engine, settings=app_settings)

    return app


app = create_app(settings)
