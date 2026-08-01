from abc import ABC, abstractmethod
from datetime import datetime

from src.modules.todo.domain.entities.todo import Todo
from src.shared.utils.cursor import CursorDirection


class TodoRepository(ABC):
    @abstractmethod
    async def get_by_id(self, todo_id: int) -> Todo | None:
        pass

    @abstractmethod
    async def get_all_by_user(self, user_id: int) -> list[Todo]:
        pass

    @abstractmethod
    async def get_by_user_cursor(
        self,
        user_id: int,
        cursor_created_at: datetime | None = None,
        cursor_id: int | None = None,
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
    async def delete(self, todo_id: int) -> None:
        pass
