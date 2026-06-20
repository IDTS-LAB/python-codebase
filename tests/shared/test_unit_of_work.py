import asyncio

from src.core.database.unit_of_work import SQLAlchemyUnitOfWork


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


def test_sqlalchemy_unit_of_work_rolls_back_when_scope_exits_without_commit():
    async def run():
        session = FakeSession()
        unit_of_work = SQLAlchemyUnitOfWork(session)

        async with unit_of_work:
            pass

        assert session.rolled_back is True
        assert session.committed is False

    asyncio.run(run())


def test_sqlalchemy_unit_of_work_does_not_roll_back_after_commit():
    async def run():
        session = FakeSession()
        unit_of_work = SQLAlchemyUnitOfWork(session)

        async with unit_of_work:
            await unit_of_work.commit()

        assert session.committed is True
        assert session.rolled_back is False

    asyncio.run(run())


def test_sqlalchemy_unit_of_work_rolls_back_and_propagates_scope_exception():
    async def run():
        session = FakeSession()
        unit_of_work = SQLAlchemyUnitOfWork(session)

        try:
            async with unit_of_work:
                raise RuntimeError("write failed")
        except RuntimeError as exc:
            assert str(exc) == "write failed"

        assert session.rolled_back is True
        assert session.committed is False

    asyncio.run(run())
