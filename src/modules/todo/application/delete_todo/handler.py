from uuid import UUID

from src.modules.todo.domain.exceptions.todo_exception import (
    TodoNotFoundError,
    UnauthorizedTodoAccessError,
)
from src.modules.todo.domain.repositories.todo_repository import TodoRepository


class DeleteTodoHandler:
    def __init__(self, todo_repo: TodoRepository):
        self.todo_repo = todo_repo

    async def execute(self, todo_id: UUID, user_id: UUID) -> None:
        todo = await self.todo_repo.get_by_id(todo_id)
        if not todo:
            raise TodoNotFoundError("Todo not found")
        if todo.user_id != user_id:
            raise UnauthorizedTodoAccessError(
                "You do not have permission to delete this todo"
            )

        await self.todo_repo.delete(todo_id)
