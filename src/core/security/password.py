from passlib.context import CryptContext

_password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class PasswordSerrvice:
    @staticmethod
    def varify(password: str, hashed_password) -> bool:
        return _password_context.verify(password, hashed_password)

    @staticmethod
    def hash(password: str) -> str:
        return _password_context.hash(password)
