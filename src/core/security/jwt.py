from datetime import datetime, timedelta, timezone
from uuid import uuid4

from jose import JWTError, jwt

from src.core.config.setting import get_settings
from src.shared.exceptions.credential_exception import InvalidCredentialsError

settings = get_settings()


class JWTService:
    ACCESS_TOKEN_TYPE = "access"
    REFRESH_TOKEN_TYPE = "refresh"

    @staticmethod
    def _create_token(data: dict, token_type: str, expires_delta: timedelta) -> str:
        now = datetime.now(timezone.utc)
        to_encode = data.copy()
        to_encode.update(
            {
                "iss": settings.JWT_ISSUER,
                "sub": str(to_encode["sub"]),
                "aud": settings.JWT_AUDIENCE,
                "exp": now + expires_delta,
                "nbf": now,
                "iat": now,
                "jti": str(uuid4()),
                "token_type": token_type,
            }
        )
        return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    @staticmethod
    def create_access_token(data: dict) -> str:
        return JWTService._create_token(
            data=data,
            token_type=JWTService.ACCESS_TOKEN_TYPE,
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        )

    @staticmethod
    def create_refresh_token(data: dict) -> str:
        return JWTService._create_token(
            data=data,
            token_type=JWTService.REFRESH_TOKEN_TYPE,
            expires_delta=timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES),
        )

    @staticmethod
    def decode_token(token: str) -> dict:
        try:
            return jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM],
                issuer=settings.JWT_ISSUER,
                audience=settings.JWT_AUDIENCE,
            )
        except JWTError:
            raise InvalidCredentialsError("Invalid or expired token")

    @staticmethod
    def require_token_type(payload: dict, expected_token_type: str) -> None:
        if payload.get("token_type") != expected_token_type:
            raise InvalidCredentialsError(f"{expected_token_type.title()} token required")
