from uuid import UUID

from src.modules.todo.domain.exceptions.todo_exception import (
    TodoNotFoundError,
    UnauthorizedTodoAccessError,
)
from src.modules.todo.domain.repositories.todo_repository import TodoRepository
from src.shared.unit_of_work import UnitOfWork


class DeleteTodoHandler:
    def __init__(self, todo_repo: TodoRepository, unit_of_work: UnitOfWork):
        self.todo_repo = todo_repo
        self._unit_of_work = unit_of_work

    async def execute(self, todo_id: UUID, user_id: UUID) -> None:
        todo = await self.todo_repo.get_by_id(todo_id)
        if not todo:
            raise TodoNotFoundError("Todo not found")
        if todo.user_id != user_id:
            raise UnauthorizedTodoAccessError(
                "You do not have permission to delete this todo"
            )

        try:
            await self.todo_repo.delete(todo_id)
            await self._unit_of_work.commit()
        except Exception:
            await self._unit_of_work.rollback()
            raise
