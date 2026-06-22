from fastapi import APIRouter, FastAPI

from src.modules.authorization.presentation.routers.permission_router import (
    router as permission_router,
)
from src.modules.authorization.presentation.routers.role_router import (
    router as role_router,
)
from src.modules.todo.presentation.routers.todo_router import router as todo_router
from src.modules.user.presentation.routers.user_router import router as user_router

router = APIRouter(prefix="/api/v1")
router.include_router(user_router)
router.include_router(todo_router)
router.include_router(role_router)
router.include_router(permission_router)


def register_router(app: FastAPI):
    app.include_router(router)
