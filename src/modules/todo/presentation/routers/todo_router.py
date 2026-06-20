from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.core.authorization.dependencies import require_permission
from src.core.authorization.permissions import (
    CREATE_ACTION,
    DELETE_ACTION,
    READ_ACTION,
    TODO_RESOURCE,
    UPDATE_ACTION,
)
from src.core.schemas.response import (
    CursorMeta,
    CursorPaginatedResponse,
    SuccessResponse,
)
from src.modules.todo.application.create_todo.command import CreateTodoCommand
from src.modules.todo.application.create_todo.handler import CreateTodoHandler
from src.modules.todo.application.delete_todo.handler import DeleteTodoHandler
from src.modules.todo.application.list_todo.handler import (
    GetTodosCursorQuery,
)
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
    get_todos_query_handler,
    get_update_todo_handler,
)
from src.modules.todo.presentation.schemas.response import TodoResponse
from src.shared.utils.cursor import CursorDirection, decode_cursor, encode_cursor

router = APIRouter(prefix="/todos", tags=["Todos"])


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=SuccessResponse[TodoResponse],
)
async def create_todo(
    command: CreateTodoCommand,
    current_user: dict = Depends(require_permission(TODO_RESOURCE, CREATE_ACTION)),
    handler: CreateTodoHandler = Depends(get_create_todo_handler),
):
    todo = await handler.execute(command, user_id=current_user.get("id"))
    return SuccessResponse(
        message="create todo success",
        success=True,
        data=TodoResponse(
            id=str(todo.id),
            title=todo.title,
            is_completed=todo.is_completed,
        ),
    )


@router.get("/", response_model=CursorPaginatedResponse[TodoResponse])
async def get_todos(
    cursor: Optional[str] = Query(
        None, description="Cursor for pagination (from previous response)"
    ),
    limit: int = Query(10, ge=1, le=100, description="Number of items per page"),
    current_user: dict = Depends(require_permission(TODO_RESOURCE, READ_ACTION)),
    query: GetTodosCursorQuery = Depends(get_todos_query_handler),
):
    cursor_created_at = None
    cursor_id = None
    direction = None
    if cursor:
        cursor_created_at, cursor_id, direction = decode_cursor(cursor)

    command = GetTodosQuery(user_id=current_user.get("id"))
    todos, has_more = await query.execute(
        user_id=command.user_id,
        cursor_created_at=cursor_created_at,
        cursor_id=cursor_id,
        limit=limit,
        direction=direction,
    )
    response_todos = [
        TodoResponse(
            id=str(t.id),
            title=t.title,
            description=t.description,
            is_completed=t.is_completed,
            created_at=t.created_at.isoformat(),
        )
        for t in todos
    ]

    next_cursor = None
    prev_cursor = None

    if has_more and len(todos) > 0:
        last_item = todos[-1]
        next_cursor = encode_cursor(
            last_item.created_at,
            last_item.id,
            CursorDirection.DIRECTION_NEXT,
        )

    if cursor and len(todos) > 0:
        first_item = todos[0]
        prev_cursor = encode_cursor(
            first_item.created_at,
            first_item.id,
            CursorDirection.DIRECTION_PREV,
        )

    return CursorPaginatedResponse(
        message="Todos retrieved successfully",
        meta=CursorMeta(
            next_cursor=next_cursor,
            prev_cursor=prev_cursor,
            has_next=has_more,
            has_prev=cursor is not None,
            limit=limit,
        ),
        data=response_todos,
    )


@router.patch("/{todo_id}", response_model=SuccessResponse[TodoResponse])
async def update_todo(
    todo_id: UUID,
    command: UpdateTodoCommand,
    current_user: dict = Depends(require_permission(TODO_RESOURCE, UPDATE_ACTION)),
    handler: UpdateTodoHandler = Depends(get_update_todo_handler),
):
    try:
        todo = await handler.execute(todo_id, command, user_id=current_user.get("id"))
        return SuccessResponse(
            message="update todo success",
            success=True,
            data=TodoResponse(
                id=str(todo.id),
                title=todo.title,
                is_completed=todo.is_completed,
            ),
        )
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
