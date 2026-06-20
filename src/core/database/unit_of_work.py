from types import TracebackType
from typing import Self

from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.unit_of_work import UnitOfWork


class SQLAlchemyUnitOfWork(UnitOfWork):
    def __init__(self, session: AsyncSession):
        self._session = session
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
