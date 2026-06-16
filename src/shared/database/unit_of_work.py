from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.unit_of_work import UnitOfWork


class SQLAlchemyUnitOfWork(UnitOfWork):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()
