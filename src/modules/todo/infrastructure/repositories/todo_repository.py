from datetime import datetime
from uuid import UUID

from sqlalchemy import and_, delete, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.todo.domain.entities.todo import Todo
from src.modules.todo.domain.repositories.todo_repository import TodoRepository
from src.modules.todo.infrastructure.models.todo_model import TodoModel
from src.shared.utils.cursor import CursorDirection


class SQLAlchemyTodoRepository(TodoRepository):
    def __init__(self, db: AsyncSession, tenant_id: UUID | None = None):
        self.db = db
        self._tenant_id = tenant_id

    async def get_by_id(self, todo_id: UUID) -> Todo | None:
        stmt = select(TodoModel).where(TodoModel.id == todo_id)
        if self._tenant_id:
            stmt = stmt.where(TodoModel.tenant_id == self._tenant_id)
        result = await self.db.execute(stmt)
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

    async def get_by_user_cursor(
        self,
        user_id: UUID,
        cursor_created_at: datetime | None = None,
        cursor_id: UUID | None = None,
        limit: int = 10,
        direction: CursorDirection = CursorDirection.DIRECTION_NEXT,
    ) -> tuple[list[Todo], bool]:
        """
        Cursor pagination logic:
        - If direction="next": Get items AFTER the cursor (older items)
        - If direction="prev": Get items BEFORE the cursor (newer items)
        """
        query = select(TodoModel).where(
            TodoModel.user_id == user_id,
            TodoModel.deleted_at.is_(None),
        )
        if self._tenant_id:
            query = query.where(TodoModel.tenant_id == self._tenant_id)

        # Apply cursor filter if provided
        if cursor_created_at and cursor_id:
            if direction == CursorDirection.DIRECTION_NEXT:
                # Get items older than cursor (created_at < cursor OR (created_at == cursor AND id < cursor_id))
                query = query.where(
                    or_(
                        TodoModel.created_at < cursor_created_at,
                        and_(
                            TodoModel.created_at == cursor_created_at,
                            TodoModel.id < cursor_id,
                        ),
                    )
                )
                query = query.order_by(TodoModel.created_at.desc(), TodoModel.id.desc())
            else:
                # Get items newer than cursor (created_at > cursor OR (created_at == cursor AND id > cursor_id))
                query = query.where(
                    or_(
                        TodoModel.created_at > cursor_created_at,
                        and_(
                            TodoModel.created_at == cursor_created_at,
                            TodoModel.id > cursor_id,
                        ),
                    )
                )
                query = query.order_by(TodoModel.created_at.asc(), TodoModel.id.asc())
        else:
            # No cursor, just get the first page
            query = query.order_by(TodoModel.created_at.desc(), TodoModel.id.desc())

        # Fetch limit + 1 to check if there are more items
        query = query.limit(limit + 1)

        result = await self.db.execute(query)
        models = result.scalars().all()

        # Check if there are more items
        has_more = len(models) > limit
        models = models[:limit]  # Trim to actual limit

        # If we fetched "prev", reverse to maintain consistent order (newest first)
        if direction == CursorDirection.DIRECTION_PREV:
            models = list(reversed(models))

        return [self._to_entity(m) for m in models], has_more

    async def get_all_by_user(self, user_id: UUID) -> list[Todo]:
        stmt = select(TodoModel).where(TodoModel.user_id == user_id)
        if self._tenant_id:
            stmt = stmt.where(TodoModel.tenant_id == self._tenant_id)
        result = await self.db.execute(stmt)
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
            tenant_id=self._tenant_id,
        )
        model = await self.db.merge(model)
        await self.db.flush()
        await self.db.refresh(model)
        return Todo(
            id=model.id,
            title=model.title,
            description=model.description,
            is_completed=model.is_completed,
            user_id=model.user_id,
        )

    async def delete(self, todo_id: UUID) -> None:
        stmt = delete(TodoModel).where(TodoModel.id == todo_id)
        if self._tenant_id:
            stmt = stmt.where(TodoModel.tenant_id == self._tenant_id)
        await self.db.execute(stmt)
        await self.db.flush()

    def _to_entity(self, model: TodoModel) -> Todo:
        return Todo(
            id=str(model.id),
            description=model.description,
            is_completed=model.is_completed,
            title=model.title,
            user_id=model.user_id,
        )
