from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.middleware.auth import AuthenticationMiddleware


def register_middleware(app: FastAPI):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],  # Your frontend URL
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(AuthenticationMiddleware)
