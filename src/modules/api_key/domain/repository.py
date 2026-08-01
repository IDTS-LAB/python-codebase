from abc import ABC, abstractmethod

from src.modules.api_key.domain.entities import ApiKey


class ApiKeyRepository(ABC):
    @abstractmethod
    async def create(self, api_key: ApiKey) -> ApiKey: ...

    @abstractmethod
    async def get_by_id(self, id: int) -> ApiKey | None: ...

    @abstractmethod
    async def get_by_key_hash(self, key_hash: str) -> ApiKey | None: ...

    @abstractmethod
    async def list(
        self, skip: int = 0, limit: int = 100
    ) -> list[ApiKey]: ...

    @abstractmethod
    async def count(self) -> int: ...

    @abstractmethod
    async def revoke(self, id: int) -> None: ...

    @abstractmethod
    async def update_last_used(self, id: int) -> None: ...
