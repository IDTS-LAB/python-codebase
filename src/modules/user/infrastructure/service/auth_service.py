from passlib.context import CryptContext

from src.core.security.jwt import JWTService

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    def verifyy_password(self, password: str, hashed_password: str) -> bool:
        return pwd_context.verify(password, hashed_password)

    def create_access_token(self, data: dict) -> str:
        return JWTService.create_access_token(data)

    def decode_token(self, token: str) -> dict:
        return JWTService.decode_token(token)
