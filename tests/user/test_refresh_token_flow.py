import asyncio
import hashlib
import inspect
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from src.modules.user.application.refresh_token.command import RefreshTokenCommand
from src.modules.user.application.refresh_token import handler as refresh_handler_module
from src.modules.user.application.refresh_token.handler import RefreshTokenCommandHandler
from src.modules.user.domain.entities.refresh_token import RefreshToken
from src.modules.user.domain.repositories.refresh_token_repository import (
    RefreshTokenRepository,
)
from src.modules.user.presentation.dependency import get_refresh_token_handler
from src.shared.exceptions.credential_exception import InvalidRefreshTokenError


class FakeRefreshTokenRepository:
    def __init__(self, stored_token=None):
        self.stored_token = stored_token
        self.saved_tokens = []

    async def get_by_token_hash(self, token_hash: str):
        if self.stored_token and self.stored_token.token_hash == token_hash:
            return self.stored_token
        return None

    async def save(self, refresh_token: RefreshToken):
        self.saved_tokens.append(refresh_token)
        return refresh_token

    async def revoke_by_user_id(self, user_id):
        return None


def test_refresh_token_command_uses_refresh_token_only():
    command = RefreshTokenCommand(token="raw-refresh-token")

    assert command.token == "raw-refresh-token"


def test_refresh_token_handler_dependency_uses_refresh_token_repository():
    dependency = inspect.signature(get_refresh_token_handler).parameters[
        "refresh_token_repo"
    ]

    assert dependency.annotation is RefreshTokenRepository


def test_refresh_token_rejects_unknown_token():
    async def run():
        handler = RefreshTokenCommandHandler(FakeRefreshTokenRepository())

        with pytest.raises(InvalidRefreshTokenError, match="Invalid refresh token"):
            await handler.execute(RefreshTokenCommand(token="unknown-token"))

    asyncio.run(run())


def test_refresh_token_rotates_token_and_revokes_existing_token():
    async def run():
        raw_token = "raw-refresh-token"
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        user_id = uuid4()
        stored_token = RefreshToken.create(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=datetime.now(timezone.utc) + timedelta(days=1),
        )
        repo = FakeRefreshTokenRepository(stored_token)

        result = await RefreshTokenCommandHandler(repo).execute(
            RefreshTokenCommand(token=raw_token)
        )

        assert result["access_token"]
        assert result["refresh_token"]
        assert stored_token.is_revoked is True
        assert repo.saved_tokens[0] is stored_token
        assert repo.saved_tokens[1].user_id == user_id
        assert repo.saved_tokens[1].is_revoked is False

    asyncio.run(run())


def test_refresh_token_rotation_persists_new_expiry_in_minutes(monkeypatch):
    async def run():
        monkeypatch.setattr(
            refresh_handler_module.settings,
            "REFRESH_TOKEN_EXPIRE_MINUTES",
            15,
        )
        raw_token = "raw-refresh-token"
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        user_id = uuid4()
        stored_token = RefreshToken.create(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=datetime.now(timezone.utc) + timedelta(days=1),
        )
        repo = FakeRefreshTokenRepository(stored_token)

        before = datetime.now(timezone.utc)
        await RefreshTokenCommandHandler(repo).execute(RefreshTokenCommand(token=raw_token))
        after = datetime.now(timezone.utc)

        new_refresh_token = repo.saved_tokens[1]
        assert before.timestamp() + (15 * 60) <= new_refresh_token.expires_at.timestamp()
        assert new_refresh_token.expires_at.timestamp() <= after.timestamp() + (15 * 60)

    asyncio.run(run())
