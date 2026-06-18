import asyncio

from src.core.middleware.auth import AuthenticationMiddleware
from src.core.security.jwt import JWTService
from src.core.security.token_revocation import TokenRevocationService
from starlette.requests import Request
from starlette.responses import JSONResponse


def test_authentication_middleware_rejects_revoked_access_token(monkeypatch):
    async def run():
        async def revoked_token(_token):
            return True

        monkeypatch.setattr(
            TokenRevocationService,
            "is_access_token_revoked",
            revoked_token,
        )

        token = JWTService.create_access_token({"sub": "user-id"})
        request = Request(
            {
                "type": "http",
                "method": "GET",
                "path": "/protected",
                "headers": [(b"authorization", f"Bearer {token}".encode())],
                "query_string": b"",
                "server": ("testserver", 80),
                "scheme": "http",
                "client": ("testclient", 50000),
            }
        )

        async def call_next(_request):
            return JSONResponse({"ok": True})

        response = await AuthenticationMiddleware(None).dispatch(request, call_next)

        assert response.status_code == 401

    asyncio.run(run())


def test_authentication_middleware_rejects_refresh_token_on_protected_endpoint(
    monkeypatch,
):
    async def run():
        async def active_token(_token):
            return False

        monkeypatch.setattr(
            TokenRevocationService,
            "is_access_token_revoked",
            active_token,
        )

        token = JWTService.create_refresh_token({"sub": "user-id"})
        call_next_called = False
        request = Request(
            {
                "type": "http",
                "method": "GET",
                "path": "/protected",
                "headers": [(b"authorization", f"Bearer {token}".encode())],
                "query_string": b"",
                "server": ("testserver", 80),
                "scheme": "http",
                "client": ("testclient", 50000),
            }
        )

        async def call_next(_request):
            nonlocal call_next_called
            call_next_called = True
            return JSONResponse({"ok": True})

        response = await AuthenticationMiddleware(None).dispatch(request, call_next)

        assert response.status_code == 401
        assert call_next_called is False

    asyncio.run(run())
