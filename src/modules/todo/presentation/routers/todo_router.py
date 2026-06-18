from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from src.core.authorization.dependencies import require_permission
from src.core.authorization.permissions import (
    CREATE_ACTION,
    DELETE_ACTION,
    READ_ACTION,
    TODO_RESOURCE,
    UPDATE_ACTION,
)
from src.modules.todo.application.create_todo.command import CreateTodoCommand
from src.modules.todo.application.create_todo.handler import CreateTodoHandler
from src.modules.todo.application.delete_todo.handler import DeleteTodoHandler
from src.modules.todo.application.list_todo.handler import GetTodosQueryHandler
from src.modules.todo.application.list_todo.query import GetTodosQuery
from src.modules.todo.application.update_todo.command import UpdateTodoCommand
from src.modules.todo.application.update_todo.handler import UpdateTodoHandler
from src.modules.todo.domain.exceptions.todo_exception import (
    TodoNotFoundError,
    UnauthorizedTodoAccessError,
)
from src.modules.todo.presentation.dependency import (
    get_create_todo_handler,
    get_delete_todo_handler,
    get_get_todos_query_handler,
    get_update_todo_handler,
)

router = APIRouter(prefix="/todos", tags=["Todos"])


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
)
async def create_todo(
    command: CreateTodoCommand,
    current_user: dict = Depends(require_permission(TODO_RESOURCE, CREATE_ACTION)),
    handler: CreateTodoHandler = Depends(get_create_todo_handler),
):
    todo = await handler.execute(command, user_id=current_user.get("id"))
    return {"id": str(todo.id), "title": todo.title, "is_completed": todo.is_completed}


@router.get("/")
async def get_todos(
    current_user: dict = Depends(require_permission(TODO_RESOURCE, READ_ACTION)),
    query: GetTodosQueryHandler = Depends(get_get_todos_query_handler),
):
    command = GetTodosQuery(user_id=current_user.get("id"))
    todos = await query.execute(command=command)
    return [
        {"id": str(t.id), "title": t.title, "is_completed": t.is_completed}
        for t in todos
    ]


@router.patch("/{todo_id}")
async def update_todo(
    todo_id: UUID,
    command: UpdateTodoCommand,
    current_user: dict = Depends(require_permission(TODO_RESOURCE, UPDATE_ACTION)),
    handler: UpdateTodoHandler = Depends(get_update_todo_handler),
):
    try:
        todo = await handler.execute(todo_id, command, user_id=current_user.get("id"))
        return {
            "id": str(todo.id),
            "title": todo.title,
            "is_completed": todo.is_completed,
            "created_at": todo.created_at,
        }
    except TodoNotFoundError:
        raise HTTPException(status_code=404, detail="Todo not found")
    except UnauthorizedTodoAccessError:
        raise HTTPException(status_code=403, detail="Forbidden")


@router.delete("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(
    todo_id: UUID,
    current_user: dict = Depends(require_permission(TODO_RESOURCE, DELETE_ACTION)),
    handler: DeleteTodoHandler = Depends(get_delete_todo_handler),
):
    try:
        await handler.execute(todo_id=todo_id, user_id=current_user.get("id"))
    except TodoNotFoundError:
        raise HTTPException(status_code=404, detail="Todo not found")
    except UnauthorizedTodoAccessError:
        raise HTTPException(status_code=403, detail="Forbidden")
