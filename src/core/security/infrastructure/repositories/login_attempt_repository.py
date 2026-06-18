from datetime import datetime

from sqlalchemy import delete, func, select

from src.core.security.infrastructure.models.login_attempt_model import (
    LoginAttemptModel,
)


class SQLAlchemyLoginAttemptRepository:
    def __init__(self, db):
        self._db = db

    async def count_failures_since(self, email: str, since: datetime) -> int:
        result = await self._db.execute(
            select(func.count())
            .select_from(LoginAttemptModel)
            .where(
                LoginAttemptModel.email == email,
                LoginAttemptModel.occurred_at >= since,
            )
        )
        return int(result.scalar_one())

    async def record_failure(
        self,
        email: str,
        occurred_at: datetime,
        locked_until: datetime | None = None,
    ) -> None:
        self._db.add(
            LoginAttemptModel(
                email=email,
                occurred_at=occurred_at,
                locked_until=locked_until,
            )
        )

    async def get_locked_until(self, email: str) -> datetime | None:
        result = await self._db.execute(
            select(LoginAttemptModel.locked_until)
            .where(
                LoginAttemptModel.email == email,
                LoginAttemptModel.locked_until.is_not(None),
            )
            .order_by(LoginAttemptModel.locked_until.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def clear(self, email: str) -> None:
        await self._db.execute(
            delete(LoginAttemptModel).where(LoginAttemptModel.email == email)
        )
