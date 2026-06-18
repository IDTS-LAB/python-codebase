from uuid import UUID

from src.modules.todo.application.update_todo.command import UpdateTodoCommand
from src.modules.todo.application.update_todo.validation import (
    validate_update_todo_command,
)
from src.modules.todo.domain.entities.todo import Todo
from src.modules.todo.domain.exceptions.todo_exception import (
    TodoNotFoundError,
    UnauthorizedTodoAccessError,
)
from src.modules.todo.domain.repositories.todo_repository import TodoRepository
from src.shared.unit_of_work import UnitOfWork


class UpdateTodoHandler:
    def __init__(self, todo_repo: TodoRepository, unit_of_work: UnitOfWork):
        self.todo_repo = todo_repo
        self._unit_of_work = unit_of_work

    async def execute(
        self, todo_id: UUID, command: UpdateTodoCommand, user_id: UUID
    ) -> Todo:
        validate_update_todo_command(command)

        todo = await self.todo_repo.get_by_id(todo_id)
        if not todo:
            raise TodoNotFoundError("Todo not found")
        if todo.user_id != user_id:
            raise UnauthorizedTodoAccessError(
                "You do not have permission to update this todo"
            )

        if command.title is not None:
            todo.title = command.title

        if command.description is not None:
            todo.description = command.description

        # TODO: move to complete_todo application
        if command.is_completed is not None:
            if command.is_completed:
                todo.mark_completed()
            else:
                todo.is_completed = False

        async with self._unit_of_work:
            saved_todo = await self.todo_repo.save(todo)
            await self._unit_of_work.commit()
            return saved_todo
