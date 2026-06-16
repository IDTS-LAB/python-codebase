from uuid import UUID

from src.modules.todo.application.create_todo.command import CreateTodoCommand
from src.modules.todo.domain.entities.todo import Todo
from src.modules.todo.domain.repositories.todo_repository import TodoRepository
from src.shared.unit_of_work import UnitOfWork


class CreateTodoHandler:
    def __init__(self, todo_repo: TodoRepository, unit_of_work: UnitOfWork):
        self.todo_repo = todo_repo
        self._unit_of_work = unit_of_work

    async def execute(self, command: CreateTodoCommand, user_id: UUID) -> Todo:
        todo = Todo.create(
            title=command.title, user_id=user_id, description=command.description
        )
        try:
            saved_todo = await self.todo_repo.save(todo)
            await self._unit_of_work.commit()
            return saved_todo
        except Exception:
            await self._unit_of_work.rollback()
            raise
