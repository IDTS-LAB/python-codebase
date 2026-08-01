from src.modules.todo import (
    TodoNotFoundError,
    TodoRepository,
    UnauthorizedTodoAccessError,
)
from src.modules.todo.presentation.schemas.response import TodoWithOwnerResponse
from src.modules.user import UserNotFoundError
from src.modules.user.facade import UserModuleFacade


class GetTodoDetailWithOwnerHandler:
    def __init__(
        self,
        todo_repo: TodoRepository,
        user_facade: UserModuleFacade,
    ):
        self._todo_repo = todo_repo
        self._user_facade = user_facade

    async def execute(self, todo_id: int, user_id: int) -> TodoWithOwnerResponse:
        todo = await self._todo_repo.get_by_id(todo_id)
        if not todo:
            raise TodoNotFoundError("Todo not found")
        if todo.user_id != user_id:
            raise UnauthorizedTodoAccessError(
                "You do not have permission to view this todo"
            )

        owner = await self._user_facade.get_user_profile(todo.user_id)
        if not owner:
            raise UserNotFoundError("Todo owner not found")

        return TodoWithOwnerResponse(
            id=todo.id,
            title=todo.title,
            description=todo.description,
            is_completed=todo.is_completed,
            owner=owner,
        )
