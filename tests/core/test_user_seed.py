from dataclasses import dataclass

import pytest

from src.core.authorization.permissions import (
    ADMIN_ROLE,
    DEFAULT_USER_ROLE,
    MANAGER_ROLE,
    VIEWER_ROLE,
)
from src.core.security.password import PasswordSerrvice
from src.core.seed.user import SeedUserConfig, seed_user
from src.modules.user.domain.entities.user import User


class FakeUserRepository:
    def __init__(self):
        self.users: dict[str, User] = {}

    async def get_by_email(self, email: str) -> User | None:
        return self.users.get(email)

    async def save(self, user: User) -> User:
        self.users[user.email] = user
        return user


class FakeAuthorizationService:
    def __init__(self):
        self.assignments: list[tuple[str, str]] = []

    async def assign_role(self, subject: str, role: str) -> None:
        self.assignments.append((subject, role))


@dataclass(frozen=True)
class SeedSettings:
    APP_ENV: str = "production"
    SEED_ADMIN_EMAIL: str = "admin@example.com"
    SEED_ADMIN_PASSWORD: str = "admin-password"
    SEED_ADMIN_USERNAME: str = "admin"
    SEED_ADMIN_FULLNAME: str = "System Administrator"
    SEED_DEVELOPMENT_USERS_PASSWORD: str = "development-password"


@pytest.mark.anyio
async def test_seed_user_creates_admin_user_with_hashed_password_and_role():
    user_repository = FakeUserRepository()
    authorization_service = FakeAuthorizationService()

    result = await seed_user(
        user_repository=user_repository,
        authorization_service=authorization_service,
        config=SeedUserConfig.from_settings(SeedSettings()),
    )

    user = user_repository.users["admin@example.com"]
    assert result.users_created == 1
    assert result.roles_assigned == 1
    assert user.username == "admin"
    assert user.fullname == "System Administrator"
    assert user.password != "admin-password"
    assert PasswordSerrvice.verify("admin-password", user.password)
    assert authorization_service.assignments == [(str(user.id), ADMIN_ROLE)]


@pytest.mark.anyio
async def test_seed_user_is_idempotent_by_email():
    user_repository = FakeUserRepository()
    authorization_service = FakeAuthorizationService()
    config = SeedUserConfig.from_settings(SeedSettings())

    await seed_user(
        user_repository=user_repository,
        authorization_service=authorization_service,
        config=config,
    )
    result = await seed_user(
        user_repository=user_repository,
        authorization_service=authorization_service,
        config=config,
    )

    assert result.users_created == 0
    assert result.roles_assigned == 0
    assert len(user_repository.users) == 1
    assert len(authorization_service.assignments) == 1


@pytest.mark.anyio
async def test_seed_user_skips_when_admin_credentials_are_missing():
    user_repository = FakeUserRepository()
    authorization_service = FakeAuthorizationService()

    result = await seed_user(
        user_repository=user_repository,
        authorization_service=authorization_service,
        config=SeedUserConfig(
            app_env="production",
            admin_email="",
            admin_password="",
            admin_username="admin",
            admin_fullname="System Administrator",
            development_users_password="development-password",
        ),
    )

    assert result.users_created == 0
    assert result.roles_assigned == 0
    assert user_repository.users == {}
    assert authorization_service.assignments == []


@pytest.mark.anyio
async def test_seed_user_creates_development_users_with_different_roles():
    user_repository = FakeUserRepository()
    authorization_service = FakeAuthorizationService()

    result = await seed_user(
        user_repository=user_repository,
        authorization_service=authorization_service,
        config=SeedUserConfig(
            app_env="development",
            admin_email="",
            admin_password="",
            admin_username="admin",
            admin_fullname="System Administrator",
            development_users_password="development-password",
        ),
    )

    assert result.users_created == 3
    assert result.roles_assigned == 3
    assert set(user_repository.users.keys()) == {
        "user@example.com",
        "manager@example.com",
        "viewer@example.com",
    }
    assert {
        role for _, role in authorization_service.assignments
    } == {DEFAULT_USER_ROLE, MANAGER_ROLE, VIEWER_ROLE}
    for user in user_repository.users.values():
        assert PasswordSerrvice.verify("development-password", user.password)


@pytest.mark.anyio
async def test_seed_user_skips_development_users_outside_development():
    user_repository = FakeUserRepository()
    authorization_service = FakeAuthorizationService()

    result = await seed_user(
        user_repository=user_repository,
        authorization_service=authorization_service,
        config=SeedUserConfig(
            app_env="production",
            admin_email="",
            admin_password="",
            admin_username="admin",
            admin_fullname="System Administrator",
            development_users_password="development-password",
        ),
    )

    assert result.users_created == 0
    assert result.roles_assigned == 0
    assert user_repository.users == {}
    assert authorization_service.assignments == []
