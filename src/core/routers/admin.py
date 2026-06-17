from fastapi import APIRouter, FastAPI

router = APIRouter(prefix="/api/admin")


def register_router(app: FastAPI):
    app.include_router(router)
