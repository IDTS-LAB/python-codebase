from datetime import datetime, timezone

from src.core.database.redis.client import get_redis_client
from src.core.security.jwt import JWTService


class TokenRevocationService:
    KEY_PREFIX = "revoked_access_token"

    @staticmethod
    def _key(jti: str) -> str:
        return f"{TokenRevocationService.KEY_PREFIX}:{jti}"

    @staticmethod
    async def revoke_access_token(token: str, redis=None) -> None:
        try:
            payload = JWTService.decode_token(token)
        except Exception:
            return

        jti = payload.get("jti")
        exp = payload.get("exp")
        if not jti or not exp:
            return

        ttl = int(exp - datetime.now(timezone.utc).timestamp())
        if ttl <= 0:
            return

        redis_client = redis or await get_redis_client()
        await redis_client.setex(TokenRevocationService._key(jti), ttl, "1")

    @staticmethod
    async def is_access_token_revoked(token: str, redis=None) -> bool:
        try:
            payload = JWTService.decode_token(token)
        except Exception:
            return False

        jti = payload.get("jti")
        if not jti:
            return False

        redis_client = redis or await get_redis_client()
        return bool(await redis_client.exists(TokenRevocationService._key(jti)))
