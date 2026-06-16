import asyncio
from datetime import datetime, timezone

from src.core.config.setting import settings
from src.core.security.password import PasswordSerrvice
from src.modules.user.application.login_user.command import LoginUserCommand
from src.modules.user.application.login_user.handler import LoginUserCommandHandler
from src.modules.user.domain.entities.user import User


class FakeUserRepository:
    def __init__(self, user):
        self.user = user

    async def get_by_email(self, email: str):
        if self.user.email == email:
            return self.user
        return None

    async def get_by_id(self, user_id):
        return self.user if self.user.id == user_id else None

    async def save(self, user):
        self.user = user
        return user


class FakeRefreshTokenRepository:
    def __init__(self):
        self.saved_token = None

    async def get_by_token_hash(self, token_hash: str):
        return None

    async def save(self, refresh_token):
        self.saved_token = refresh_token
        return refresh_token

    async def revoke_by_user_id(self, user_id):
        return None


def test_login_persists_refresh_token_expiry_in_minutes(monkeypatch):
    async def run():
        monkeypatch.setattr(settings, "REFRESH_TOKEN_EXPIRE_MINUTES", 15)
        user = User.create(
            email="person@example.com",
            password=PasswordSerrvice.hash("plain-secret"),
        )
        refresh_token_repo = FakeRefreshTokenRepository()

        before = datetime.now(timezone.utc)
        result = await LoginUserCommandHandler(
            FakeUserRepository(user),
            refresh_token_repo,
        ).execute(
            LoginUserCommand(
                username="person@example.com",
                password="plain-secret",
            )
        )
        after = datetime.now(timezone.utc)

        assert result["access_token"]
        assert result["refresh_token"]
        expires_at = refresh_token_repo.saved_token.expires_at.timestamp()
        assert before.timestamp() + (15 * 60) <= expires_at
        assert expires_at <= after.timestamp() + (15 * 60)

    asyncio.run(run())
