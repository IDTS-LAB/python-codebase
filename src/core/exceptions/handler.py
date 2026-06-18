from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from src.core.schemas.response import ErrorDetail, ErrorResponse
from src.modules.todo.domain.exceptions.todo_exception import (
    TodoNotFoundError,
    UnauthorizedTodoAccessError,
)

# Import your custom domain exceptions here
from src.modules.user.domain.exceptions.user_exception import UserAlreadyExistsError
from src.shared.exceptions.credential_exception import (
    InvalidCredentialsError,
    InvalidRefreshTokenError,
)

# Map domain exceptions to HTTP status codes and error codes
DOMAIN_EXCEPTION_MAP = {
    UserAlreadyExistsError: (status.HTTP_400_BAD_REQUEST, "USER_ALREADY_EXISTS"),
    InvalidCredentialsError: (status.HTTP_401_UNAUTHORIZED, "INVALID_CREDENTIALS"),
    InvalidRefreshTokenError: (status.HTTP_401_UNAUTHORIZED, "INVALID_REFRESH_TOKEN"),
    TodoNotFoundError: (status.HTTP_404_NOT_FOUND, "TODO_NOT_FOUND"),
    UnauthorizedTodoAccessError: (
        status.HTTP_403_FORBIDDEN,
        "UNAUTHORIZED_TODO_ACCESS",
    ),
}


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handles Pydantic validation errors (e.g., missing fields, wrong types)"""
    details = [
        ErrorDetail(field=".".join(str(loc) for loc in err["loc"]), message=err["msg"])
        for err in exc.errors()
    ]
    response, status_code = ErrorResponse.create(
        code="VALIDATION_ERROR",
        message="Request payload validation failed",
        details=details,
        http_status=status.HTTP_422_UNPROCESSABLE_ENTITY,
    )
    return JSONResponse(status_code=status_code, content=response.model_dump())


async def http_exception_handler(request: Request, exc):
    """Handles standard FastAPI HTTPExceptions"""
    response, status_code = ErrorResponse.create(
        code="HTTP_ERROR", message=exc.detail, http_status=exc.status_code
    )
    return JSONResponse(status_code=status_code, content=response.model_dump())


async def domain_exception_handler(request: Request, exc: Exception):
    """Handles custom Domain Exceptions"""
    exc_type = type(exc)
    if exc_type in DOMAIN_EXCEPTION_MAP:
        status_code, code = DOMAIN_EXCEPTION_MAP[exc_type]
    else:
        status_code, code = (
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "UNKNOWN_DOMAIN_ERROR",
        )

    response, _ = ErrorResponse.create(
        code=code, message=str(exc), http_status=status_code
    )
    return JSONResponse(status_code=status_code, content=response.model_dump())


async def global_exception_handler(request: Request, exc: Exception):
    """Fallback for any unhandled exceptions (e.g., Database errors, 3rd party API failures)"""
    # Log the actual error here in production (e.g., Sentry, Datadog)
    # logger.error(f"Unhandled exception: {exc}", exc_info=True)

    response, status_code = ErrorResponse.create(
        code="INTERNAL_SERVER_ERROR",
        message="An unexpected error occurred. Please try again later.",
        http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
    return JSONResponse(status_code=status_code, content=response.model_dump())
