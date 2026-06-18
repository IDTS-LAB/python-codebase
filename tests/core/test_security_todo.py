import pytest
from fastapi import FastAPI, Request

from src.core.bootstrap.exception import register_exception
from src.core.bootstrap.middleware import register_middleware
from src.core.config.setting import Settings
from src.core.dependency import rate_limit as rate_limit_module
from src.core.dependency.rate_limit import apply_global_rate_limit
from src.core.exceptions.handler import (
    DOMAIN_EXCEPTION_MAP,
    domain_exception_handler,
    global_exception_handler,
)
from src.main import create_app


def test_rate_limit_uses_configured_rate_limit_setting(monkeypatch):
    created_limiters = []

    class FakeLimiter:
        def __init__(self, times: int, seconds: int):
            self.times = times
            self.seconds = seconds
            created_limiters.append(self)

        async def __call__(self, request):
            return None

    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/api/v1/todos/",
            "headers": [],
            "query_string": b"",
            "server": ("testserver", 80),
            "scheme": "http",
            "client": ("testclient", 50000),
        }
    )

    monkeypatch.setattr(rate_limit_module.settings, "RATE_LIMIT", "42/minute")
    monkeypatch.setattr(rate_limit_module, "RateLimiter", FakeLimiter)

    import asyncio

    asyncio.run(apply_global_rate_limit(request))

    assert created_limiters[0].times == 42
    assert created_limiters[0].seconds == 60


def test_cors_middleware_uses_environment_driven_settings(monkeypatch):
    monkeypatch.setattr(
        "src.core.bootstrap.middleware.settings",
        Settings(
            CORS_ALLOW_ORIGINS="https://app.example.com,https://admin.example.com",
            CORS_ALLOW_METHODS="GET,POST",
            CORS_ALLOW_HEADERS="Authorization,Content-Type",
        ),
    )
    app = FastAPI()

    register_middleware(app)

    cors = next(
        middleware
        for middleware in app.user_middleware
        if middleware.cls.__name__ == "CORSMiddleware"
    )
    assert cors.kwargs["allow_origins"] == [
        "https://app.example.com",
        "https://admin.example.com",
    ]
    assert cors.kwargs["allow_methods"] == ["GET", "POST"]
    assert cors.kwargs["allow_headers"] == ["Authorization", "Content-Type"]


def test_register_exception_uses_specific_domain_handlers_and_single_fallback():
    app = FastAPI()

    register_exception(app)

    for exception_type in DOMAIN_EXCEPTION_MAP:
        assert app.exception_handlers[exception_type] is domain_exception_handler
    assert app.exception_handlers[Exception] is global_exception_handler


def test_create_app_disables_openapi_entrypoints_in_production():
    app = create_app(Settings(APP_ENV="production", SECRET_KEY="production-secret"))

    assert app.docs_url is None
    assert app.redoc_url is None
    assert app.openapi_url is None


def test_production_settings_reject_default_secret_key():
    with pytest.raises(ValueError, match="SECRET_KEY must be changed"):
        Settings(
            APP_ENV="production",
            SECRET_KEY=Settings.DEFAULT_SECRET_KEY,
            _env_file=None,
        )


def test_production_settings_reject_wildcard_cors():
    with pytest.raises(ValueError, match="CORS_ALLOW_ORIGINS"):
        Settings(
            APP_ENV="production",
            SECRET_KEY="production-secret",
            CORS_ALLOW_ORIGINS="*",
            _env_file=None,
        )


def test_production_settings_reject_invalid_token_ttl():
    with pytest.raises(ValueError, match="ACCESS_TOKEN_EXPIRE_MINUTES"):
        Settings(
            APP_ENV="production",
            SECRET_KEY="production-secret",
            ACCESS_TOKEN_EXPIRE_MINUTES=0,
            _env_file=None,
        )


def test_production_settings_reject_missing_service_urls():
    with pytest.raises(ValueError, match="DATABASE_URL"):
        Settings(
            APP_ENV="production",
            SECRET_KEY="production-secret",
            DATABASE_URL="",
            _env_file=None,
        )
