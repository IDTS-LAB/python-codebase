from fastapi import status
from jose import JWTError
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from src.core.security.jwt import JWTService
from src.core.security.token_revocation import TokenRevocationService
from src.shared.exceptions.credential_exception import InvalidCredentialsError

PUBLIC_PATHS = frozenset(
    {
        "/health",
        "/docs",
        "/docs/",
        "/redoc",
        "/redoc/",
        "/openapi.json",
        "/api/v1/auth/login",
        "/api/v1/auth/register",
        "/api/v1/auth/refresh",
    }
)


class AuthenticationMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        if request.method == "OPTIONS":
            return await call_next(request)

        path = request.url.path.rstrip("/")
        if path in PUBLIC_PATHS:
            return await call_next(request)

        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Authorization header missing or malformed"},
            )

        token = auth_header.split(" ", 1)[1]

        try:
            payload = JWTService.decode_token(token)
            JWTService.require_token_type(payload, JWTService.ACCESS_TOKEN_TYPE)
            if await TokenRevocationService.is_access_token_revoked(token):
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Token has been revoked"},
                )

            user_id = payload.get("sub")
            if not user_id:
                raise ValueError("Token missing 'sub' claim")

            request.state.user_id = user_id
            request.state.token_payload = payload
        except JWTError as e:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": f"Invalid or expired token: {str(e)}"},
            )
        except InvalidCredentialsError as e:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": str(e)},
            )
        except Exception:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Authentication failed"},
            )

        response = await call_next(request)
        return response
