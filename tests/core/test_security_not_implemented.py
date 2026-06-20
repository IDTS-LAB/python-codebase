import asyncio
import json
import logging
from datetime import datetime, timezone

import pytest
from starlette.requests import Request
from starlette.responses import JSONResponse

from src.core.config.setting import Settings
from src.core.middleware.auth import AuthenticationMiddleware
from src.core.middleware.idempotency import IdempotencyMiddleware
from src.core.middleware.request_id import RequestIDMiddleware
from src.core.middleware.security_headers import SecurityHeadersMiddleware
from src.core.middleware.structured_logging import StructuredLoggingMiddleware
from src.core.routers import admin as admin_router
from src.core.security.account_lockout import AccountLockoutService
from src.core.security.audit import AuditEvent, AuditService


def test_security_headers_middleware_adds_expected_headers():
    async def run():
        request = Request(
            {
                "type": "http",
                "method": "GET",
                "path": "/health",
                "headers": [],
                "query_string": b"",
                "server": ("testserver", 80),
                "scheme": "http",
                "client": ("testclient", 50000),
            }
        )

        async def call_next(_request):
            return JSONResponse({"ok": True})

        response = await SecurityHeadersMiddleware(None).dispatch(request, call_next)

        assert response.headers["x-content-type-options"] == "nosniff"
        assert response.headers["x-frame-options"] == "DENY"
        assert response.headers["referrer-policy"] == "no-referrer"
        assert "default-src" in response.headers["content-security-policy"]

    asyncio.run(run())


def test_request_id_middleware_propagates_existing_request_id():
    async def run():
        request = Request(
            {
                "type": "http",
                "method": "GET",
                "path": "/health",
                "headers": [(b"x-request-id", b"request-123")],
                "query_string": b"",
                "server": ("testserver", 80),
                "scheme": "http",
                "client": ("testclient", 50000),
            }
        )

        async def call_next(received_request):
            assert received_request.state.request_id == "request-123"
            return JSONResponse({"ok": True})

        response = await RequestIDMiddleware(None).dispatch(request, call_next)

        assert response.headers["x-request-id"] == "request-123"

    asyncio.run(run())


def test_structured_logging_middleware_logs_request_context(caplog):
    async def run():
        caplog.set_level(logging.INFO, logger="src.core.middleware.structured_logging")
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
        request.state.request_id = "request-123"
        request.state.user_id = "user-123"

        async def call_next(_request):
            return JSONResponse({"ok": True}, status_code=202)

        await StructuredLoggingMiddleware(None).dispatch(request, call_next)

    asyncio.run(run())

    record = caplog.records[0]
    assert record.method == "GET"
    assert record.path == "/api/v1/todos/"
    assert record.status_code == 202
    assert record.request_id == "request-123"
    assert record.user_id == "user-123"


def test_structured_logging_middleware_logs_exception_context(caplog):
    async def run():
        caplog.set_level(logging.ERROR, logger="src.core.middleware.structured_logging")
        request = Request(
            {
                "type": "http",
                "method": "POST",
                "path": "/api/v1/todos/",
                "headers": [],
                "query_string": b"",
                "server": ("testserver", 80),
                "scheme": "http",
                "client": ("testclient", 50000),
            }
        )
        request.state.request_id = "request-456"
        request.state.user_id = "user-456"

        async def call_next(_request):
            raise RuntimeError("write failed")

        with pytest.raises(RuntimeError, match="write failed"):
            await StructuredLoggingMiddleware(None).dispatch(request, call_next)

    asyncio.run(run())

    record = caplog.records[0]
    assert record.method == "POST"
    assert record.path == "/api/v1/todos/"
    assert record.status_code == 500
    assert record.request_id == "request-456"
    assert record.user_id == "user-456"
    assert record.error_type == "RuntimeError"


def test_structured_logging_formats_record_as_json():
    from src.core.middleware.structured_logging import JsonLogFormatter

    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="request completed",
        args=(),
        exc_info=None,
    )
    record.method = "GET"
    record.path = "/api/v1/todos/"
    record.status_code = 200
    record.latency_ms = 1.5
    record.request_id = "request-1"
    record.user_id = "user-1"
    record.error_type = None

    payload = json.loads(JsonLogFormatter().format(record))

    assert payload["message"] == "request completed"
    assert payload["method"] == "GET"
    assert payload["path"] == "/api/v1/todos/"
    assert payload["status_code"] == 200
    assert payload["request_id"] == "request-1"


def test_admin_router_exposes_liveness_and_readiness(monkeypatch):
    class FakeConnection:
        async def exec_driver_sql(self, statement):
            return None

    class FakeEngine:
        def connect(self):
            class ConnectionContext:
                async def __aenter__(self):
                    return FakeConnection()

                async def __aexit__(self, exc_type, exc, traceback):
                    return False

            return ConnectionContext()

    class FakeRedis:
        async def ping(self):
            return True

    async def fake_get_redis_client():
        return FakeRedis()

    monkeypatch.setattr(admin_router, "engine", FakeEngine())
    monkeypatch.setattr(admin_router, "get_redis_client", fake_get_redis_client)

    async def run():
        live_response = await admin_router.live()
        ready_response = await admin_router.ready()

        assert live_response == {"status": "alive"}
        assert ready_response.status_code == 200
        assert json.loads(ready_response.body.decode()) == {
            "status": "ready",
            "checks": {"database": "ok", "redis": "ok"},
        }

    asyncio.run(run())


def test_authentication_middleware_returns_generic_invalid_token_error():
    async def run():
        request = Request(
            {
                "type": "http",
                "method": "GET",
                "path": "/protected",
                "headers": [(b"authorization", b"Bearer invalid-token")],
                "query_string": b"",
                "server": ("testserver", 80),
                "scheme": "http",
                "client": ("testclient", 50000),
            }
        )

        async def call_next(_request):
            return JSONResponse({"ok": True})

        response = await AuthenticationMiddleware(None).dispatch(request, call_next)
        body = json.loads(response.body.decode())

        assert response.status_code == 401
        assert body["detail"] == "Invalid or expired token"

    asyncio.run(run())


class FakeAuditRepository:
    def __init__(self):
        self.events = []

    async def save(self, event):
        self.events.append(event)
        return event


def test_audit_service_persists_sensitive_event():
    async def run():
        repo = FakeAuditRepository()
        service = AuditService(repo)
        event = AuditEvent(
            action="user.login",
            actor_id="user-1",
            resource_type="user",
            resource_id="user-1",
            request_id="request-1",
            metadata={"result": "success"},
        )

        await service.record(event)

        assert repo.events == [event]

    asyncio.run(run())


class FakeLoginAttemptRepository:
    def __init__(self):
        self.failures = {}
        self.locked_until = {}
        self.cleared = []

    async def count_failures_since(self, email, since):
        return self.failures.get(email, 0)

    async def record_failure(self, email, occurred_at, locked_until=None):
        self.failures[email] = self.failures.get(email, 0) + 1
        if locked_until is not None:
            self.locked_until[email] = locked_until

    async def get_locked_until(self, email):
        return self.locked_until.get(email)

    async def clear(self, email):
        self.cleared.append(email)
        self.failures.pop(email, None)
        self.locked_until.pop(email, None)


def test_account_lockout_locks_after_configured_failures():
    async def run():
        repo = FakeLoginAttemptRepository()
        settings = Settings(
            ACCOUNT_LOCKOUT_MAX_ATTEMPTS=2,
            ACCOUNT_LOCKOUT_WINDOW_MINUTES=5,
            ACCOUNT_LOCKOUT_DURATION_MINUTES=15,
        )
        service = AccountLockoutService(repo, settings)

        await service.record_failed_login("person@example.com")
        await service.record_failed_login("person@example.com")

        assert repo.locked_until["person@example.com"] > datetime.now(timezone.utc)
        with pytest.raises(ValueError, match="temporarily locked"):
            await service.ensure_login_allowed("person@example.com")

    asyncio.run(run())


class FakeRedis:
    def __init__(self):
        self.values = {}

    async def get(self, key):
        return self.values.get(key)

    async def set(self, key, value, ex=None, nx=False):
        if nx and key in self.values:
            return False
        self.values[key] = value
        return True

    async def setex(self, key, ttl, value):
        self.values[key] = value


def build_post_request(body: bytes):
    async def receive():
        return {"type": "http.request", "body": body, "more_body": False}

    return Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/api/v1/todos/",
            "headers": [
                (b"idempotency-key", b"create-todo-1"),
                (b"authorization", b"Bearer token"),
                (b"content-type", b"application/json"),
            ],
            "query_string": b"",
            "server": ("testserver", 80),
            "scheme": "http",
            "client": ("testclient", 50000),
        },
        receive,
    )


def test_idempotency_middleware_replays_cached_post_response():
    async def run():
        redis = FakeRedis()
        calls = 0
        async def call_next(_request):
            nonlocal calls
            calls += 1
            return JSONResponse({"created": True}, status_code=201)

        middleware = IdempotencyMiddleware(None, redis=redis)
        first = await middleware.dispatch(
            build_post_request(b'{"title":"first"}'),
            call_next,
        )
        second = await middleware.dispatch(
            build_post_request(b'{"title":"first"}'),
            call_next,
        )

        assert first.status_code == 201
        assert second.status_code == 201
        assert json.loads(second.body.decode()) == {"created": True}
        assert calls == 1

    asyncio.run(run())


def test_idempotency_middleware_rejects_same_key_with_different_body():
    async def run():
        redis = FakeRedis()
        calls = 0

        async def call_next(_request):
            nonlocal calls
            calls += 1
            return JSONResponse({"created": True}, status_code=201)

        middleware = IdempotencyMiddleware(None, redis=redis)
        first = await middleware.dispatch(
            build_post_request(b'{"title":"first"}'),
            call_next,
        )
        second = await middleware.dispatch(
            build_post_request(b'{"title":"second"}'),
            call_next,
        )

        assert first.status_code == 201
        assert second.status_code == 409
        assert json.loads(second.body.decode())["detail"] == (
            "Idempotency-Key was already used with a different request body"
        )
        assert calls == 1

    asyncio.run(run())
