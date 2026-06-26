from types import TracebackType
from typing import TYPE_CHECKING, Self
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.unit_of_work import UnitOfWork

if TYPE_CHECKING:
    from src.modules.todo.domain.repositories.todo_repository import TodoRepository
    from src.modules.user.domain.repositories.user_repository import UserRepository


class SQLAlchemyUnitOfWork(UnitOfWork):
    def __init__(self, session: AsyncSession, tenant_id: UUID | None = None):
        self._session = session
        self._tenant_id = tenant_id
        self._committed = False

    async def __aenter__(self) -> Self:
        self._committed = False
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool:
        if exc_type is not None or not self._committed:
            await self.rollback()
        return False

    async def commit(self) -> None:
        await self._session.commit()
        self._committed = True

    async def rollback(self) -> None:
        await self._session.rollback()

    @property
    def users(self) -> "UserRepository":
        from src.modules.user.infrastructure.repositories.user_repository import (
            SQLAlchemyUserRepository,
        )

        return SQLAlchemyUserRepository(self._session, self._tenant_id)

    @property
    def todos(self) -> "TodoRepository":
        from src.modules.todo.infrastructure.repositories.todo_repository import (
            SQLAlchemyTodoRepository,
        )

        return SQLAlchemyTodoRepository(self._session, self._tenant_id)
