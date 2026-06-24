import hashlib
import hmac
import secrets
import time
from abc import ABC, abstractmethod

from src.core.config.setting import get_settings

settings = get_settings()


class CSRFService(ABC):
    @abstractmethod
    def generate_token(self) -> str: ...

    @abstractmethod
    def validate_token(self, token: str, cookie_token: str) -> bool: ...


class DoubleSubmitCSRFService(CSRFService):
    def generate_token(self) -> str:
        return secrets.token_urlsafe(32)

    def validate_token(self, token: str, cookie_token: str) -> bool:
        if not token or not cookie_token:
            return False
        return hmac.compare_digest(token, cookie_token)


class SignedCSRFService(CSRFService):
    def generate_token(self) -> str:
        raw = secrets.token_urlsafe(16)
        sig = self._sign(raw)
        return f"{raw}.{sig}"

    def validate_token(self, token: str, cookie_token: str) -> bool:
        try:
            raw, sig = token.rsplit(".", 1)
            expected = self._sign(raw)
            return hmac.compare_digest(sig, expected) and hmac.compare_digest(
                token, cookie_token
            )
        except (ValueError, AttributeError):
            return False

    @staticmethod
    def _sign(value: str) -> str:
        return hashlib.sha256(
            f"{value}:{settings.SECRET_KEY}:csrf:{int(time.time()) // 86400}".encode()
        ).hexdigest()[:16]
