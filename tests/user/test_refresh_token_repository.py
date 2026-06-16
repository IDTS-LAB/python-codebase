import asyncio
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from src.modules.user.domain.entities.refresh_token import RefreshToken
from src.modules.user.infrastructure.repositories.refresh_token_repository import (
    SQLAlchemyRefreshTokenRepository,
)


class FakeSession:
    def __init__(self):
        self.added_model = None
        self.merged_model = None
        self.committed = False
        self.flushed = False
        self.refreshed_model = None

    def add(self, model):
        self.added_model = model

    async def merge(self, model):
        self.merged_model = model
        return model

    async def commit(self):
        self.committed = True

    async def flush(self):
        self.flushed = True

    async def refresh(self, model):
        self.refreshed_model = model


def test_refresh_token_save_merges_existing_identity():
    async def run():
        session = FakeSession()
        repository = SQLAlchemyRefreshTokenRepository(session)
        refresh_token = RefreshToken.create(
            user_id=uuid4(),
            token_hash="token-hash",
            expires_at=datetime.now(timezone.utc) + timedelta(days=1),
        )

        saved_token = await repository.save(refresh_token)

        assert session.added_model is None
        assert session.merged_model is not None
        assert session.committed is False
        assert session.flushed is True
        assert session.refreshed_model is session.merged_model
        assert saved_token.id == refresh_token.id

    asyncio.run(run())
