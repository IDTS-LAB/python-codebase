from fastapi import FastAPI

from src.core.middleware.auth import PUBLIC_PATHS
from src.core.routers.api.v1 import register_router
from src.modules.user.presentation.dependency import oauth2_scheme


def test_register_router_groups_module_routes_under_api_v1():
    app = FastAPI()

    register_router(app)

    included_router = app.routes[-1]
    route_paths = {
        route.path for route in included_router.effective_route_contexts()
    }
    assert "/api/v1/auth/login" in route_paths
    assert "/api/v1/auth/register" in route_paths
    assert "/api/v1/todos/" in route_paths
    assert "/auth/login" not in route_paths
    assert "/todos/" not in route_paths


def test_auth_entrypoints_under_api_v1_are_public():
    assert "/api/v1/auth/login" in PUBLIC_PATHS
    assert "/api/v1/auth/register" in PUBLIC_PATHS
    assert "/auth/login" not in PUBLIC_PATHS
    assert "/auth/register" not in PUBLIC_PATHS


def test_oauth2_password_flow_points_to_api_v1_login():
    assert oauth2_scheme.model.flows.password.tokenUrl == "/api/v1/auth/login"
