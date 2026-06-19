import asyncio
from uuid import uuid4

from src.modules.user.application.logout_user.command import LogoutUserCommand
from src.modules.user.application.logout_user.handler import LogoutUserCommandHandler


class FakeRefreshTokenRepository:
    def __init__(self):
        self.revoked_user_ids = []

    async def revoke_by_user_id(self, user_id):
        self.revoked_user_ids.append(user_id)


class FakeTokenRevocationService:
    def __init__(self):
        self.revoked_access_tokens = []

    async def revoke_access_token(self, token):
        self.revoked_access_tokens.append(token)


class FakeUnitOfWork:
    def __init__(self):
        self.committed = False
        self.rolled_back = False

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        if exc_type is not None or not self.committed:
            await self.rollback()
        return False

    async def commit(self):
        self.committed = True

    async def rollback(self):
        self.rolled_back = True


def test_logout_revokes_refresh_tokens_and_current_access_token():
    async def run():
        user_id = str(uuid4())
        refresh_token_repo = FakeRefreshTokenRepository()
        token_revocation_service = FakeTokenRevocationService()
        unit_of_work = FakeUnitOfWork()

        await LogoutUserCommandHandler(
            refresh_token_repo,
            unit_of_work,
            token_revocation_service,
        ).execute(
            LogoutUserCommand(
                user_id=user_id,
                access_token="current-access-token",
            )
        )

        assert refresh_token_repo.revoked_user_ids == [user_id]
        assert token_revocation_service.revoked_access_tokens == ["current-access-token"]
        assert unit_of_work.committed is True
        assert unit_of_work.rolled_back is False

    asyncio.run(run())
