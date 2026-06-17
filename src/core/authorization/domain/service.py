from abc import ABC, abstractmethod


class AuthorizationService(ABC):
    @abstractmethod
    async def can(self, subject: str, resource: str, action: str) -> bool:
        pass

    @abstractmethod
    async def assign_role(self, subject: str, role: str) -> None:
        pass

    @abstractmethod
    async def get_roles_for_subject(self, subject: str) -> list[str]:
        pass
