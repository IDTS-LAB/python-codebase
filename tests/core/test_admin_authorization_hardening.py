from src.modules.authorization.presenter.routers.permission_router import (
    router as permission_router,
)
from src.modules.authorization.presenter.routers.role_router import router as role_router


def test_role_and_permission_management_routes_require_dependencies():
    routes = [
        route
        for route in [*role_router.routes, *permission_router.routes]
        if hasattr(route, "dependencies")
    ]

    assert routes
    for route in routes:
        assert route.dependencies, f"{route.path} has no authorization dependency"
