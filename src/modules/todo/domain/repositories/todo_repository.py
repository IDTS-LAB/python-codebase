from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID

from src.core.utils.cursor import CursorDirection
from src.modules.todo.domain.entities.todo import Todo


class TodoRepository(ABC):
    @abstractmethod
    async def get_by_id(self, todo_id: UUID) -> Todo | None:
        pass

    @abstractmethod
    async def get_all_by_user(self, user_id: UUID) -> list[Todo]:
        pass

    @abstractmethod
    async def get_by_user_cursor(
        self,
        user_id: UUID,
        cursor_created_at: datetime | None = None,
        cursor_id: UUID | None = None,
        limit: int = 10,
        direction: CursorDirection = CursorDirection.DIRECTION_NEXT,
    ) -> tuple[list[Todo], bool]:
        """
        Get todos with cursor pagination.
        Returns: (items, has_more)
        """
        pass

    @abstractmethod
    async def save(self, todo: Todo) -> Todo:
        pass

    @abstractmethod
    async def delete(self, todo_id: UUID) -> None:
        pass
