import asyncio
from datetime import datetime, timedelta, timezone

from jose import jwt

from src.core.config.setting import get_settings
from src.core.security.jwt import JWTService
from src.core.security.token_revocation import TokenRevocationService

settings = get_settings()


class FakeRedis:
    def __init__(self):
        self.values = {}
        self.ttls = {}

    async def setex(self, key, ttl, value):
        self.values[key] = value
        self.ttls[key] = ttl

    async def exists(self, key):
        return int(key in self.values)


def test_access_tokens_include_unique_jti_claims():
    first_token = JWTService.create_access_token({"sub": "user-id"})
    second_token = JWTService.create_access_token({"sub": "user-id"})

    first_payload = JWTService.decode_token(first_token)
    second_payload = JWTService.decode_token(second_token)

    assert first_payload["jti"]
    assert second_payload["jti"]
    assert first_payload["jti"] != second_payload["jti"]


def test_token_revocation_stores_access_token_jti_until_expiry():
    async def run():
        redis = FakeRedis()
        token = JWTService.create_access_token({"sub": "user-id"})
        payload = JWTService.decode_token(token)

        await TokenRevocationService.revoke_access_token(token, redis)

        key = f"revoked_access_token:{payload['jti']}"
        assert redis.values[key] == "1"
        assert redis.ttls[key] > 0
        assert await TokenRevocationService.is_access_token_revoked(token, redis) is True

    asyncio.run(run())


def test_token_revocation_ignores_already_expired_tokens():
    async def run():
        redis = FakeRedis()
        token = jwt.encode(
            {
                "sub": "user-id",
                "jti": "expired-token-id",
                "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
            },
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM,
        )

        await TokenRevocationService.revoke_access_token(token, redis)

        assert redis.values == {}

    asyncio.run(run())
