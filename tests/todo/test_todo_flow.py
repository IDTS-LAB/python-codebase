import asyncio
import inspect
from uuid import uuid4

import pytest
from fastapi import HTTPException

from src.modules.todo.application.delete_todo.handler import DeleteTodoHandler
from src.modules.todo.domain.entities.todo import Todo
from src.modules.todo.infrastructure.repositories.todo_repository import (
    SQLAlchemyTodoRepository,
)
from src.modules.todo.presentation.routers.todo_router import delete_todo


class FakeTodoRepository:
    def __init__(self, todo=None):
        self.todo = todo
        self.deleted_id = None

    async def get_by_id(self, todo_id):
        if self.todo and self.todo.id == todo_id:
            return self.todo
        return None

    async def delete(self, todo_id):
        self.deleted_id = todo_id


def test_delete_todo_checks_ownership_before_delete():
    async def run():
        owner_id = uuid4()
        todo = Todo.create(title="Task", user_id=owner_id)
        repo = FakeTodoRepository(todo)

        await delete_todo(
            todo_id=todo.id,
            current_user={"id": owner_id},
            handler=DeleteTodoHandler(repo),
        )

        assert repo.deleted_id == todo.id

    asyncio.run(run())


def test_delete_todo_rejects_missing_todo():
    async def run():
        repo = FakeTodoRepository()

        with pytest.raises(HTTPException) as exc_info:
            await delete_todo(
                todo_id=uuid4(),
                current_user={"id": uuid4()},
                handler=DeleteTodoHandler(repo),
            )

        assert exc_info.value.status_code == 404

    asyncio.run(run())


def test_delete_todo_rejects_wrong_owner():
    async def run():
        todo = Todo.create(title="Task", user_id=uuid4())
        repo = FakeTodoRepository(todo)

        with pytest.raises(HTTPException) as exc_info:
            await delete_todo(
                todo_id=todo.id,
                current_user={"id": uuid4()},
                handler=DeleteTodoHandler(repo),
            )

        assert exc_info.value.status_code == 403

    asyncio.run(run())


def test_todo_repository_save_uses_merge_for_upsert():
    source = inspect.getsource(SQLAlchemyTodoRepository.save)

    assert ".merge(" in source
