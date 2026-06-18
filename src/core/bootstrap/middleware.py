from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.config.setting import get_settings
from src.core.middleware.auth import AuthenticationMiddleware
from src.core.middleware.audit_logging import AuditLoggingMiddleware
from src.core.middleware.idempotency import IdempotencyMiddleware
from src.core.middleware.request_id import RequestIDMiddleware
from src.core.middleware.request_size import LimitRequestSizeMiddleware
from src.core.middleware.security_headers import SecurityHeadersMiddleware
from src.core.middleware.structured_logging import StructuredLoggingMiddleware

settings = get_settings()


def register_middleware(app: FastAPI):
    app.add_middleware(
        LimitRequestSizeMiddleware,
        max_upload_size=settings.MAX_REQUEST_SIZE_MB,
    )
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allow_origins,
        allow_credentials=True,
        allow_methods=settings.cors_allow_methods,
        allow_headers=settings.cors_allow_headers,
    )
    app.add_middleware(IdempotencyMiddleware)
    app.add_middleware(StructuredLoggingMiddleware)
    app.add_middleware(AuditLoggingMiddleware)
    app.add_middleware(AuthenticationMiddleware)
    app.add_middleware(RequestIDMiddleware)
