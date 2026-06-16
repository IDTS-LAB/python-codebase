import asyncio

from src.shared.database.unit_of_work import SQLAlchemyUnitOfWork


class FakeSession:
    def __init__(self):
        self.committed = False
        self.rolled_back = False

    async def commit(self):
        self.committed = True

    async def rollback(self):
        self.rolled_back = True


def test_sqlalchemy_unit_of_work_commits_session():
    async def run():
        session = FakeSession()
        unit_of_work = SQLAlchemyUnitOfWork(session)

        await unit_of_work.commit()

        assert session.committed is True

    asyncio.run(run())


def test_sqlalchemy_unit_of_work_rolls_back_session():
    async def run():
        session = FakeSession()
        unit_of_work = SQLAlchemyUnitOfWork(session)

        await unit_of_work.rollback()

        assert session.rolled_back is True

    asyncio.run(run())
