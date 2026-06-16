from passlib.context import CryptContext

_password_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


class PasswordSerrvice:
    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        return _password_context.verify(password, hashed_password)

    verify = verify_password

    @staticmethod
    def hash(password: str) -> str:
        return _password_context.hash(password)
