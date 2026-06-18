from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.config.setting import get_settings
from src.core.middleware.request_size import LimitRequestSizeMiddleware
from src.core.middleware.auth import AuthenticationMiddleware

settings = get_settings()


def register_middleware(app: FastAPI):
    app.add_middleware(
        LimitRequestSizeMiddleware,
        max_upload_size=settings.MAX_REQUEST_SIZE_MB,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allow_origins,
        allow_credentials=True,
        allow_methods=settings.cors_allow_methods,
        allow_headers=settings.cors_allow_headers,
    )
    app.add_middleware(AuthenticationMiddleware)
