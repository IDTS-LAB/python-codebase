import asyncio
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from src.core.utils.cursor import CursorDirection, decode_cursor, encode_cursor
from src.modules.authorization.domain.entities.permission import Permission
from src.modules.authorization.domain.entities.role import Role
from src.modules.authorization.presenter.routers.permission_router import (
    list_permissions,
)
from src.modules.authorization.presenter.routers.role_router import list_roles


class FakeAuthorizationService:
    def __init__(self, roles=None, permissions=None):
        self.roles = roles or []
        self.permissions = permissions or []

    async def list_roles_cursor(
        self,
        cursor_created_at=None,
        cursor_id=None,
        limit=10,
        direction=None,
    ):
        return self.roles[:limit], len(self.roles) > limit

    async def list_permissions_cursor(
        self,
        cursor_created_at=None,
        cursor_id=None,
        limit=10,
        direction=None,
    ):
        return self.permissions[:limit], len(self.permissions) > limit


def test_list_roles_uses_cursor_paginated_response():
    async def run():
        now = datetime.now(UTC)
        roles = [
            Role(
                id=uuid4(),
                name=f"role-{index}",
                description=None,
                created_at=(now - timedelta(minutes=index)).isoformat(),
                updated_at=(now - timedelta(minutes=index)).isoformat(),
            )
            for index in range(3)
        ]

        response = await list_roles(
            cursor=None,
            limit=2,
            service=FakeAuthorizationService(roles),
        )

        assert response.data[0].id == str(roles[0].id)
        assert len(response.data) == 2
        assert response.meta.limit == 2
        assert response.meta.has_next is True
        assert response.meta.has_prev is False

        cursor_created_at, cursor_id, direction = decode_cursor(
            response.meta.next_cursor
        )
        assert cursor_created_at == datetime.fromisoformat(roles[1].created_at)
        assert cursor_id == roles[1].id
        assert direction == CursorDirection.DIRECTION_NEXT

    asyncio.run(run())


def test_list_permissions_exposes_previous_cursor_when_cursor_is_provided():
    async def run():
        now = datetime.now(UTC)
        permissions = [
            Permission(
                id=uuid4(),
                key=f"todo:action-{index}",
                resource="todo",
                action=f"action-{index}",
                description=None,
                created_at=(now - timedelta(minutes=index)).isoformat(),
                updated_at=(now - timedelta(minutes=index)).isoformat(),
            )
            for index in range(2)
        ]
        cursor = encode_cursor(
            datetime.fromisoformat(permissions[0].created_at),
            permissions[0].id,
            CursorDirection.DIRECTION_NEXT,
        )

        response = await list_permissions(
            cursor=cursor,
            limit=2,
            service=FakeAuthorizationService(permissions=permissions),
        )

        assert len(response.data) == 2
        assert response.meta.has_next is False
        assert response.meta.has_prev is True

        cursor_created_at, cursor_id, direction = decode_cursor(
            response.meta.prev_cursor
        )
        assert cursor_created_at == datetime.fromisoformat(permissions[0].created_at)
        assert cursor_id == permissions[0].id
        assert direction == CursorDirection.DIRECTION_PREV

    asyncio.run(run())
