from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.core.exceptions.handler import (
    domain_exception_handler,
    global_exception_handler,
    http_exception_handler,
    validation_exception_handler,
)


def register_exception(app: FastAPI):
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)

    # Catches custom domain exceptions
    app.add_exception_handler(Exception, domain_exception_handler)

    # Fallback (Note: order matters, put specific ones first)
    app.add_exception_handler(Exception, global_exception_handler)
