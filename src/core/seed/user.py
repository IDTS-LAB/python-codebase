from dataclasses import dataclass
from typing import Protocol

from src.core.authorization.permissions import ADMIN_ROLE
from src.core.security.password import PasswordSerrvice
from src.modules.user.domain.entities.user import User


class SeedUserRepository(Protocol):
    async def get_by_email(self, email: str) -> User | None:
        raise NotImplementedError

    async def save(self, user: User) -> User:
        raise NotImplementedError


class SeedAuthorizationService(Protocol):
    async def assign_role(self, subject: str, role: str) -> None:
        raise NotImplementedError


@dataclass(frozen=True)
class SeedUserConfig:
    admin_email: str
    admin_password: str
    admin_username: str | None = None
    admin_fullname: str | None = None

    @classmethod
    def from_settings(cls, settings) -> "SeedUserConfig":
        return cls(
            admin_email=settings.SEED_ADMIN_EMAIL,
            admin_password=settings.SEED_ADMIN_PASSWORD,
            admin_username=settings.SEED_ADMIN_USERNAME,
            admin_fullname=settings.SEED_ADMIN_FULLNAME,
        )

    @property
    def has_admin_credentials(self) -> bool:
        return bool(self.admin_email.strip() and self.admin_password.strip())


@dataclass(frozen=True)
class UserSeedResult:
    users_created: int = 0
    roles_assigned: int = 0


async def seed_user(
    user_repository: SeedUserRepository,
    authorization_service: SeedAuthorizationService,
    config: SeedUserConfig,
) -> UserSeedResult:
    if not config.has_admin_credentials:
        return UserSeedResult()

    existing = await user_repository.get_by_email(config.admin_email)
    if existing is not None:
        return UserSeedResult()

    user = User.create(
        email=config.admin_email,
        password=PasswordSerrvice.hash(config.admin_password),
        username=config.admin_username,
        fullname=config.admin_fullname,
    )
    saved_user = await user_repository.save(user)
    await authorization_service.assign_role(str(saved_user.id), ADMIN_ROLE)

    return UserSeedResult(users_created=1, roles_assigned=1)
