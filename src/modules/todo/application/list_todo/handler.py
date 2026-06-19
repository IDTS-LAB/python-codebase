from datetime import datetime
from uuid import UUID

from src.core.utils.cursor import CursorDirection
from src.modules.todo.application.list_todo.query import GetTodosQuery
from src.modules.todo.application.list_todo.validation import validate_get_todos_query
from src.modules.todo.domain.entities.todo import Todo
from src.modules.todo.domain.repositories.todo_repository import TodoRepository


class GetTodosQueryHandler:
    def __init__(self, todo_repo: TodoRepository):
        self.todo_repo = todo_repo

    async def execute(self, command: GetTodosQuery) -> list[Todo]:
        validate_get_todos_query(command)

        return await self.todo_repo.get_all_by_user(command.user_id)


class GetTodosCursorQuery:
    def __init__(self, todo_repo: TodoRepository):
        self.todo_repo = todo_repo

    async def execute(
        self,
        user_id: UUID,
        cursor_created_at: datetime | None = None,
        cursor_id: UUID | None = None,
        limit: int = 10,
        direction: CursorDirection = CursorDirection.DIRECTION_NEXT,
    ) -> tuple[list[Todo], bool]:
        """
        Returns: (items, has_more)
        """
        return await self.todo_repo.get_by_user_cursor(
            user_id=user_id,
            cursor_created_at=cursor_created_at,
            cursor_id=cursor_id,
            limit=limit,
            direction=direction,
        )
