from fastapi import Depends, FastAPI

import src.core.routers.admin as admin_router
import src.core.routers.api.v1 as v1_router
from src.core import lifespan
from src.core.bootstrap.exception import register_exception
from src.core.bootstrap.middleware import register_middleware
from src.core.config.setting import get_settings
from src.core.dependency.rate_limit import apply_global_rate_limit

settings = get_settings()


def create_app(app_settings=settings) -> FastAPI:
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

    @app.get("/health", tags=["Health Check"])
    def health_check():
        return {"status": "healthy"}

    return app


app = create_app(settings)
