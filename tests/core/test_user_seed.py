from dataclasses import dataclass

import pytest

from src.core.authorization.permissions import ADMIN_ROLE
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
    SEED_ADMIN_EMAIL: str = "admin@example.com"
    SEED_ADMIN_PASSWORD: str = "admin-password"
    SEED_ADMIN_USERNAME: str = "admin"
    SEED_ADMIN_FULLNAME: str = "System Administrator"


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
            admin_email="",
            admin_password="",
            admin_username="admin",
            admin_fullname="System Administrator",
        ),
    )

    assert result.users_created == 0
    assert result.roles_assigned == 0
    assert user_repository.users == {}
    assert authorization_service.assignments == []
