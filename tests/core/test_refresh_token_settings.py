from datetime import datetime, timezone

from jose import jwt

from src.core.config.setting import get_settings
from src.core.security import jwt as jwt_module
from src.core.security.jwt import JWTService

settings = get_settings()


def test_refresh_token_expiry_setting_is_minutes_based():
    assert settings.REFRESH_TOKEN_EXPIRE_MINUTES
    assert not hasattr(settings, "REFRESH_TOKEN_EXPIRE_DAYS")


def test_refresh_token_jwt_expiry_uses_minutes_setting(monkeypatch):
    monkeypatch.setattr(settings, "REFRESH_TOKEN_EXPIRE_MINUTES", 15)

    before = datetime.now(timezone.utc)
    token = JWTService.create_refresh_token({"sub": "user-id"})
    after = datetime.now(timezone.utc)

    claims = jwt.get_unverified_claims(token)
    expires_at = datetime.fromtimestamp(claims["exp"], tz=timezone.utc)

    assert before.timestamp() + (15 * 60) - 1 <= expires_at.timestamp()
    assert expires_at.timestamp() <= after.timestamp() + (15 * 60)
    assert (
        "REFRESH_TOKEN_EXPIRE_DAYS"
        not in jwt_module.JWTService.create_refresh_token.__code__.co_names
    )
