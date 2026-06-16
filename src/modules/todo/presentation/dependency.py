from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from modules.todo.application.create_todo.handler import CreateTodoHandler
from modules.todo.application.list_todo.handler import GetTodosQueryHandler
from modules.todo.application.update_todo.handler import UpdateTodoHandler
from modules.todo.domain.repositories.todo_repository import TodoRepository
from modules.todo.infrastucture.repositories.user_repository import (
    SQLAlchemyTodoRepository,
)
from src.core.database import get_db


def get_todo_repository(db: AsyncSession = Depends(get_db)) -> TodoRepository:
    return SQLAlchemyTodoRepository(db)


def get_create_todo_handler(
    repo: TodoRepository = Depends(get_todo_repository),
) -> CreateTodoHandler:
    return CreateTodoHandler(repo)


def get_update_todo_handler(
    repo: TodoRepository = Depends(get_todo_repository),
) -> UpdateTodoHandler:
    return UpdateTodoHandler(repo)


def get_get_todos_query_handler(
    repo: TodoRepository = Depends(get_todo_repository),
) -> GetTodosQueryHandler:
    return GetTodosQueryHandler(repo)
