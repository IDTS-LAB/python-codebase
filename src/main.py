from fastapi import FastAPI

import src.core.routers.api.v1 as v1_router
from src.core import lifespan
from src.core.bootstrap.middleware import register_middleware
from src.core.config.setting import settings

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    lifespan=lifespan.lifespan,
    swagger_ui_parameters={
        "persistAuthorization": True,
        "displayRequestDuration": True,
        "filter": True,
        "deepLinking": True,
        "tryItOutEnabled": True,
    },
)

register_middleware(app=app)
v1_router.register_router(app=app)


@app.get("/health", tags=["Health Check"])
def health_check():
    return {"status": "healthy"}
