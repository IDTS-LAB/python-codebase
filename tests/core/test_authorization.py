import asyncio
from uuid import uuid4

import pytest
from fastapi import HTTPException

from src.core.authorization.dependencies import require_permission


class FakeAuthorizationService:
    def __init__(self, allowed: bool):
        self.allowed = allowed
        self.calls = []

    async def can(self, subject: str, resource: str, action: str) -> bool:
        self.calls.append((subject, resource, action))
        return self.allowed


def test_require_permission_returns_current_user_when_allowed():
    async def run():
        user_id = uuid4()
        service = FakeAuthorizationService(allowed=True)
        dependency = require_permission("todo", "create")

        current_user = await dependency(
            current_user={"id": user_id},
            authorization_service=service,
        )

        assert current_user == {"id": user_id}
        assert service.calls == [(str(user_id), "todo", "create")]

    asyncio.run(run())


def test_require_permission_rejects_forbidden_user():
    async def run():
        user_id = uuid4()
        service = FakeAuthorizationService(allowed=False)
        dependency = require_permission("todo", "delete")

        with pytest.raises(HTTPException) as exc_info:
            await dependency(
                current_user={"id": user_id},
                authorization_service=service,
            )

        assert exc_info.value.status_code == 403
        assert service.calls == [(str(user_id), "todo", "delete")]

    asyncio.run(run())
