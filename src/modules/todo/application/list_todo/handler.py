from src.modules.todo.application.list_todo.query import GetTodosQuery
from src.modules.todo.domain.repositories.todo_repository import TodoRepository
from src.modules.todo.domain.entities.todo import Todo


class GetTodosQueryHandler:
    def __init__(self, todo_repo: TodoRepository):
        self.todo_repo = todo_repo

    async def execute(self, command: GetTodosQuery) -> list[Todo]:
        return await self.todo_repo.get_all_by_user(command.user_id)
