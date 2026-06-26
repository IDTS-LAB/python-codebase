from fastapi import APIRouter, FastAPI

from src.modules.api_key.presentation.routers import router as apikey_router

admin_router = APIRouter()
admin_router.include_router(apikey_router)


def register_router(app: FastAPI):
    app.include_router(admin_router)
