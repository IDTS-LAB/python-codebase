from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from src.core.config.setting import settings
from src.shared.exceptions.credential_exception import InvalidCredentialsError


class JWTService:
    @staticmethod
    def create_access_token(data: dict) -> str:
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    @staticmethod
    def decode_token(token: str) -> dict:
        try:
            return jwt.decode(
                token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
            )
        except JWTError:
            raise InvalidCredentialsError("Invalid or expired token")
