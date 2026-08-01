import asyncio

from src.core.seed.user import SeedUserConfig, seed_user
from src.modules.authorization.domain.permissions import (
    ADMIN_ROLE,
    DEFAULT_USER_ROLE,
    MANAGER_ROLE,
    VIEWER_ROLE,
)
from src.modules.user.domain.entities.user import User, UserProfile


class FakeUserRepository:
    def __init__(self, existing_users: tuple[User, ...] = ()) -> None:
        self.users = {user.email: user for user in existing_users}
        self.saved_users: list[User] = []
        self.saved_profiles: list[UserProfile] = []

    async def get_by_email(self, email: str) -> User | None:
        return self.users.get(email)

    async def save(self, user: User) -> User:
        self.users[user.email] = user
        self.saved_users.append(user)
        return user

    async def save_profile(self, profile: UserProfile) -> UserProfile:
        self.saved_profiles.append(profile)
        return profile


class FakeAuthorizationService:
    def __init__(self) -> None:
        self.assignments: list[tuple[str, str]] = []

    async def assign_role(self, subject: str, role: str) -> None:
        self.assignments.append((subject, role))


def test_seed_user_creates_admin_with_normalized_profile(monkeypatch):
    monkeypatch.setattr(
        "src.core.seed.user.PasswordSerrvice.hash",
        lambda password: f"hashed:{password}",
    )
    repository = FakeUserRepository()
    authorization = FakeAuthorizationService()

    result = asyncio.run(
        seed_user(
            user_repository=repository,
            authorization_service=authorization,
            config=SeedUserConfig(
                app_env="production",
                admin_email="admin@example.com",
                admin_password="secret-password",
                admin_username="admin",
                admin_fullname="System Administrator",
            ),
        )
    )

    assert result.users_created == 1
    assert result.roles_assigned == 1
    assert len(repository.saved_users) == 1
    saved_user = repository.saved_users[0]
    assert saved_user.email == "admin@example.com"
    assert saved_user.username == "admin"
    assert saved_user.password_hash == "hashed:secret-password"
    assert repository.saved_profiles == [
        UserProfile(user_id=saved_user.id, display_name="System Administrator")
    ]
    assert authorization.assignments == [(str(saved_user.id), ADMIN_ROLE)]


def test_seed_user_creates_development_users_and_profiles(monkeypatch):
    monkeypatch.setattr(
        "src.core.seed.user.PasswordSerrvice.hash",
        lambda password: f"hashed:{password}",
    )
    repository = FakeUserRepository()
    authorization = FakeAuthorizationService()

    result = asyncio.run(
        seed_user(
            user_repository=repository,
            authorization_service=authorization,
            config=SeedUserConfig(
                app_env="development",
                admin_email="",
                admin_password="",
                development_users_password="demo-password",
            ),
        )
    )

    assert result.users_created == 3
    assert result.roles_assigned == 3
    assert [user.email for user in repository.saved_users] == [
        "user@example.com",
        "manager@example.com",
        "viewer@example.com",
    ]
    assert [profile.display_name for profile in repository.saved_profiles] == [
        "Default User",
        "Todo Manager",
        "Todo Viewer",
    ]
    assert [role for _, role in authorization.assignments] == [
        DEFAULT_USER_ROLE,
        MANAGER_ROLE,
        VIEWER_ROLE,
    ]


def test_seed_user_does_not_modify_an_existing_user(monkeypatch):
    monkeypatch.setattr(
        "src.core.seed.user.PasswordSerrvice.hash",
        lambda password: f"hashed:{password}",
    )
    existing_user = User(
        id=1,
        email="admin@example.com",
        password_hash="existing-hash",
        username="existing-admin",
    )
    repository = FakeUserRepository((existing_user,))
    authorization = FakeAuthorizationService()

    result = asyncio.run(
        seed_user(
            user_repository=repository,
            authorization_service=authorization,
            config=SeedUserConfig(
                app_env="production",
                admin_email="admin@example.com",
                admin_password="new-password",
                admin_username="admin",
                admin_fullname="System Administrator",
            ),
        )
    )

    assert result.users_created == 0
    assert result.roles_assigned == 0
    assert repository.saved_users == []
    assert repository.saved_profiles == []
    assert authorization.assignments == []
    assert repository.users[existing_user.email] == existing_user


def test_seed_user_skips_users_without_credentials():
    repository = FakeUserRepository()
    authorization = FakeAuthorizationService()

    result = asyncio.run(
        seed_user(
            user_repository=repository,
            authorization_service=authorization,
            config=SeedUserConfig(
                app_env="production",
                admin_email="",
                admin_password="",
            ),
        )
    )

    assert result.users_created == 0
    assert result.roles_assigned == 0
    assert repository.saved_users == []
    assert repository.saved_profiles == []
    assert authorization.assignments == []
