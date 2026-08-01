from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database.postgres.session import get_db, get_unit_of_work
from src.core.dependency.tenant import get_current_tenant_id
from src.core.dependency.facades import get_user_module_facade
from src.modules.todo.application.create_todo.handler import CreateTodoHandler
from src.modules.todo.application.delete_todo.handler import DeleteTodoHandler
from src.modules.todo.application.detail_todo.handler import (
    GetTodoDetailWithOwnerHandler,
)
from src.modules.todo.application.list_todo.handler import (
    GetTodosCursorQuery,
)
from src.modules.todo.application.update_todo.handler import UpdateTodoHandler
from src.modules.todo.domain.repositories.todo_repository import TodoRepository
from src.modules.todo.infrastructure.repositories.todo_repository import (
    SQLAlchemyTodoRepository,
)
from src.modules.user.facade import UserModuleFacade
from src.shared.unit_of_work import UnitOfWork


def get_todo_repository(
    db: AsyncSession = Depends(get_db),
    tenant_id: int = Depends(get_current_tenant_id),
) -> TodoRepository:
    return SQLAlchemyTodoRepository(db, tenant_id)


def get_create_todo_handler(
    repo: TodoRepository = Depends(get_todo_repository),
    unit_of_work: UnitOfWork = Depends(get_unit_of_work),
) -> CreateTodoHandler:
    return CreateTodoHandler(repo, unit_of_work)


def get_update_todo_handler(
    repo: TodoRepository = Depends(get_todo_repository),
    unit_of_work: UnitOfWork = Depends(get_unit_of_work),
) -> UpdateTodoHandler:
    return UpdateTodoHandler(repo, unit_of_work)


def get_delete_todo_handler(
    repo: TodoRepository = Depends(get_todo_repository),
    unit_of_work: UnitOfWork = Depends(get_unit_of_work),
) -> DeleteTodoHandler:
    return DeleteTodoHandler(repo, unit_of_work)


def get_todo_detail_with_owner_handler(
    todo_repo: TodoRepository = Depends(get_todo_repository),
    user_facade: UserModuleFacade = Depends(get_user_module_facade),
) -> GetTodoDetailWithOwnerHandler:
    return GetTodoDetailWithOwnerHandler(todo_repo, user_facade=user_facade)


def get_todos_query_handler(
    repo: TodoRepository = Depends(get_todo_repository),
) -> GetTodosCursorQuery:
    return GetTodosCursorQuery(repo)
