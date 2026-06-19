import asyncio

import pytest
from starlette.requests import Request
from starlette.responses import JSONResponse

from src.core.middleware.audit_logging import AuditLoggingMiddleware


class FakeAuditService:
    def __init__(self):
        self.events = []

    async def record(self, event):
        self.events.append(event)


class FakeErrorTraceService:
    def __init__(self):
        self.traces = []

    async def record(self, trace):
        self.traces.append(trace)


def build_request(path="/api/v1/todos/123", method="PATCH"):
    request = Request(
        {
            "type": "http",
            "method": method,
            "path": path,
            "headers": [
                (b"user-agent", b"pytest"),
                (b"x-forwarded-for", b"10.0.0.1"),
            ],
            "query_string": b"",
            "server": ("testserver", 80),
            "scheme": "http",
            "client": ("testclient", 50000),
            "path_params": {"todo_id": "123"},
        }
    )
    request.state.request_id = "request-1"
    request.state.user_id = "user-1"
    return request


def test_global_audit_logging_records_api_request():
    async def run():
        audit_service = FakeAuditService()
        middleware = AuditLoggingMiddleware(
            None,
            audit_service_factory=lambda: audit_service,
        )

        async def call_next(_request):
            return JSONResponse({"ok": True}, status_code=202)

        response = await middleware.dispatch(build_request(), call_next)

        assert response.status_code == 202
        event = audit_service.events[0]
        assert event.action == "PATCH /api/v1/todos/123"
        assert event.actor_id == "user-1"
        assert event.resource_type == "todos"
        assert event.resource_id == "123"
        assert event.request_id == "request-1"
        assert event.metadata["status_code"] == 202
        assert event.metadata["client_ip"] == "10.0.0.1"
        assert event.metadata["user_agent"] == "pytest"

    asyncio.run(run())


def test_global_audit_logging_skips_operational_paths():
    async def run():
        audit_service = FakeAuditService()
        middleware = AuditLoggingMiddleware(
            None,
            audit_service_factory=lambda: audit_service,
        )

        async def call_next(_request):
            return JSONResponse({"status": "healthy"})

        await middleware.dispatch(build_request(path="/health", method="GET"), call_next)

        assert audit_service.events == []

    asyncio.run(run())


def test_global_audit_logging_records_error_trace_and_reraises():
    async def run():
        audit_service = FakeAuditService()
        error_trace_service = FakeErrorTraceService()
        middleware = AuditLoggingMiddleware(
            None,
            audit_service_factory=lambda: audit_service,
            error_trace_service_factory=lambda: error_trace_service,
        )

        async def call_next(_request):
            raise RuntimeError("database unavailable")

        with pytest.raises(RuntimeError, match="database unavailable"):
            await middleware.dispatch(build_request(), call_next)

        trace = error_trace_service.traces[0]
        assert trace.error_type == "RuntimeError"
        assert trace.message == "database unavailable"
        assert "RuntimeError: database unavailable" in trace.traceback
        assert trace.request_id == "request-1"
        assert trace.actor_id == "user-1"
        assert trace.path == "/api/v1/todos/123"

    asyncio.run(run())
