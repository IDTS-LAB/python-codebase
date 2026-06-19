from dataclasses import dataclass
from typing import Protocol

from src.core.authorization.permissions import (
    ADMIN_ROLE,
    DEFAULT_USER_ROLE,
    MANAGER_ROLE,
    VIEWER_ROLE,
)
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
    app_env: str
    admin_email: str
    admin_password: str
    admin_username: str | None = None
    admin_fullname: str | None = None
    development_users_password: str = ""

    @classmethod
    def from_settings(cls, settings) -> "SeedUserConfig":
        return cls(
            app_env=settings.APP_ENV,
            admin_email=settings.SEED_ADMIN_EMAIL,
            admin_password=settings.SEED_ADMIN_PASSWORD,
            admin_username=settings.SEED_ADMIN_USERNAME,
            admin_fullname=settings.SEED_ADMIN_FULLNAME,
            development_users_password=settings.SEED_DEVELOPMENT_USERS_PASSWORD,
        )

    @property
    def has_admin_credentials(self) -> bool:
        return bool(self.admin_email.strip() and self.admin_password.strip())

    @property
    def should_seed_development_users(self) -> bool:
        return (
            self.app_env.lower() == "development"
            and bool(self.development_users_password.strip())
        )


@dataclass(frozen=True)
class UserSeedResult:
    users_created: int = 0
    roles_assigned: int = 0


async def seed_user(
    user_repository: SeedUserRepository,
    authorization_service: SeedAuthorizationService,
    config: SeedUserConfig,
) -> UserSeedResult:
    users_created = 0
    roles_assigned = 0

    if not config.has_admin_credentials:
        admin_result = UserSeedResult()
    else:
        admin_result = await _seed_one_user(
            user_repository=user_repository,
            authorization_service=authorization_service,
            email=config.admin_email,
            password=config.admin_password,
            username=config.admin_username,
            fullname=config.admin_fullname,
            role=ADMIN_ROLE,
        )
    users_created += admin_result.users_created
    roles_assigned += admin_result.roles_assigned

    if config.should_seed_development_users:
        for development_user in _development_users(config.development_users_password):
            result = await _seed_one_user(
                user_repository=user_repository,
                authorization_service=authorization_service,
                email=development_user.email,
                password=development_user.password,
                username=development_user.username,
                fullname=development_user.fullname,
                role=development_user.role,
            )
            users_created += result.users_created
            roles_assigned += result.roles_assigned

    return UserSeedResult(users_created=users_created, roles_assigned=roles_assigned)


@dataclass(frozen=True)
class DevelopmentSeedUser:
    email: str
    password: str
    username: str
    fullname: str
    role: str


def _development_users(password: str) -> tuple[DevelopmentSeedUser, ...]:
    return (
        DevelopmentSeedUser(
            email="user@example.com",
            password=password,
            username="user",
            fullname="Default User",
            role=DEFAULT_USER_ROLE,
        ),
        DevelopmentSeedUser(
            email="manager@example.com",
            password=password,
            username="manager",
            fullname="Todo Manager",
            role=MANAGER_ROLE,
        ),
        DevelopmentSeedUser(
            email="viewer@example.com",
            password=password,
            username="viewer",
            fullname="Todo Viewer",
            role=VIEWER_ROLE,
        ),
    )


async def _seed_one_user(
    user_repository: SeedUserRepository,
    authorization_service: SeedAuthorizationService,
    email: str,
    password: str,
    username: str | None,
    fullname: str | None,
    role: str,
) -> UserSeedResult:
    existing = await user_repository.get_by_email(email)
    if existing is not None:
        return UserSeedResult()

    user = User.create(
        email=email,
        password=PasswordSerrvice.hash(password),
        username=username,
        fullname=fullname,
    )
    saved_user = await user_repository.save(user)
    await authorization_service.assign_role(str(saved_user.id), role)

    return UserSeedResult(users_created=1, roles_assigned=1)
