from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from modules.todo.domain.repositories.todo_repository import TodoRepository
from modules.todo.infrastucture.models.todo_model import TodoModel
from src.modules.todo.domain.entities import Todo


class SQLAlchemyTodoRepository(TodoRepository):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, todo_id: UUID) -> Todo | None:
        result = await self.db.execute(select(TodoModel).where(TodoModel.id == todo_id))
        model = result.scalar_one_or_none()
        if not model:
            return None
        return Todo(
            id=model.id,
            title=model.title,
            description=model.description,
            is_completed=model.is_completed,
            user_id=model.user_id,
        )

    async def get_all_by_user(self, user_id: UUID) -> list[Todo]:
        result = await self.db.execute(
            select(TodoModel).where(TodoModel.user_id == user_id)
        )
        models = result.scalars().all()
        return [
            Todo(
                id=m.id,
                title=m.title,
                description=m.description,
                is_completed=m.is_completed,
                user_id=m.user_id,
            )
            for m in models
        ]

    async def save(self, todo: Todo) -> Todo:
        model = TodoModel(
            id=todo.id,
            title=todo.title,
            description=todo.description,
            is_completed=todo.is_completed,
            user_id=todo.user_id,
        )
        self.db.add(model)
        await self.db.commit()
        await self.db.refresh(model)
        return Todo(
            id=model.id,
            title=model.title,
            description=model.description,
            is_completed=model.is_completed,
            user_id=model.user_id,
        )

    async def delete(self, todo_id: UUID) -> None:
        await self.db.execute(delete(TodoModel).where(TodoModel.id == todo_id))
        await self.db.commit()
