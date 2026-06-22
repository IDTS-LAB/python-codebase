from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from src.modules.user.domain.entities.user import User, UserProfile, UserSettings, UserSecurity


class UserRepository(ABC):
    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[User]:
        pass

    @abstractmethod
    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        pass

    @abstractmethod
    async def get_by_id_with_relations(self, user_id: UUID) -> Optional[User]:
        """Get user with profile, settings, and security loaded."""
        pass

    @abstractmethod
    async def save(self, user: User) -> User:
        pass

    @abstractmethod
    async def save_profile(self, profile: UserProfile) -> UserProfile:
        pass

    @abstractmethod
    async def save_settings(self, settings: UserSettings) -> UserSettings:
        pass

    @abstractmethod
    async def save_security(self, security: UserSecurity) -> UserSecurity:
        pass
