import hashlib
import secrets
from datetime import datetime, timezone
from typing import Optional

from src.modules.api_key.domain.entities import ApiKey
from src.modules.api_key.domain.repository import ApiKeyRepository

API_KEY_PREFIX = "api_"


class ApiKeyService:
    def __init__(self, repository: ApiKeyRepository):
        self._repository = repository

    async def generate(
        self,
        name: str,
        permissions: list[str] | None = None,
        expires_at: Optional[datetime] = None,
    ) -> tuple[ApiKey, str]:
        raw_bytes = secrets.token_bytes(32)
        raw_key = API_KEY_PREFIX + raw_bytes.hex()
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        key_prefix = raw_key[: len(API_KEY_PREFIX) + 8]

        api_key = ApiKey(
            name=name,
            key_prefix=key_prefix,
            key_hash=key_hash,
            permissions=permissions or [],
            expires_at=expires_at,
        )

        await self._repository.create(api_key)
        return api_key, raw_key

    async def validate(self, raw_key: str) -> ApiKey | None:
        if not raw_key.startswith(API_KEY_PREFIX):
            return None

        computed_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        api_key = await self._repository.get_by_key_hash(computed_hash)
        if api_key is None:
            return None
        if not api_key.is_active:
            return None
        if api_key.expires_at and api_key.expires_at < datetime.now(timezone.utc):
            return None

        await self._repository.update_last_used(api_key.id)
        return api_key
