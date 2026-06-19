from datetime import datetime, timezone

from src.core.security.jwt import JWTService


def test_access_token_uses_standard_claim_payload():
    token = JWTService.create_access_token({"sub": "user-id"})

    claims = JWTService.decode_token(token)

    assert claims["sub"] == "user-id"
    assert claims["iss"]
    assert claims["aud"]
    assert claims["token_type"] == "access"
    assert claims["jti"]
    assert claims["iat"]
    assert claims["nbf"]
    assert claims["exp"]
    assert claims["nbf"] <= claims["iat"]
    assert claims["iat"] <= claims["exp"]


def test_refresh_token_uses_standard_claim_payload():
    token = JWTService.create_refresh_token({"sub": "user-id"})

    claims = JWTService.decode_token(token)

    assert claims["sub"] == "user-id"
    assert claims["iss"]
    assert claims["aud"]
    assert claims["token_type"] == "refresh"
    assert claims["jti"]
    assert claims["iat"]
    assert claims["nbf"]
    assert claims["exp"]
    assert claims["nbf"] <= claims["iat"]
    assert claims["iat"] <= claims["exp"]


def test_token_claim_expiry_is_timezone_aware_epoch_timestamp():
    token = JWTService.create_access_token({"sub": "user-id"})

    claims = JWTService.decode_token(token)
    expires_at = datetime.fromtimestamp(claims["exp"], tz=timezone.utc)
    issued_at = datetime.fromtimestamp(claims["iat"], tz=timezone.utc)

    assert expires_at.tzinfo == timezone.utc
    assert issued_at.tzinfo == timezone.utc
