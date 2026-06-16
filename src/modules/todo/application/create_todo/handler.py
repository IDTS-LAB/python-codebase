from uuid import UUID

from src.modules.todo.application.create_todo.command import CreateTodoCommand
from src.modules.todo.domain.entities.todo import Todo
from src.modules.todo.domain.repositories.todo_repository import TodoRepository


class CreateTodoHandler:
    def __init__(self, todo_repo: TodoRepository):
        self.todo_repo = todo_repo

    async def execute(self, command: CreateTodoCommand, user_id: UUID) -> Todo:
        todo = Todo.create(
            title=command.title, user_id=user_id, description=command.description
        )
        return await self.todo_repo.save(todo)
