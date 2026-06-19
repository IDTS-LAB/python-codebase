from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.core.exceptions.handler import (
    DOMAIN_EXCEPTION_MAP,
    domain_exception_handler,
    global_exception_handler,
    http_exception_handler,
    validation_exception_handler,
)


def register_exception(app: FastAPI):
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)

    for exception_type in DOMAIN_EXCEPTION_MAP:
        app.add_exception_handler(exception_type, domain_exception_handler)

    app.add_exception_handler(Exception, global_exception_handler)
