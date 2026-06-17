from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database.postgres.session import get_db, get_unit_of_work
from src.modules.todo.application.create_todo.handler import CreateTodoHandler
from src.modules.todo.application.delete_todo.handler import DeleteTodoHandler
from src.modules.todo.application.list_todo.handler import GetTodosQueryHandler
from src.modules.todo.application.update_todo.handler import UpdateTodoHandler
from src.modules.todo.domain.repositories.todo_repository import TodoRepository
from src.modules.todo.infrastructure.repositories.todo_repository import (
    SQLAlchemyTodoRepository,
)
from src.shared.unit_of_work import UnitOfWork


def get_todo_repository(db: AsyncSession = Depends(get_db)) -> TodoRepository:
    return SQLAlchemyTodoRepository(db)


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


def get_get_todos_query_handler(
    repo: TodoRepository = Depends(get_todo_repository),
) -> GetTodosQueryHandler:
    return GetTodosQueryHandler(repo)
