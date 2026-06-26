from datetime import datetime

from sqlalchemy import delete, func, select

from uuid import UUID

from src.core.security.infrastructure.models.login_attempt_model import (
    LoginAttemptModel,
)


class SQLAlchemyLoginAttemptRepository:
    def __init__(self, db, tenant_id: UUID | None = None):
        self._db = db
        self._tenant_id = tenant_id

    async def count_failures_since(self, email: str, since: datetime) -> int:
        stmt = (
            select(func.count())
            .select_from(LoginAttemptModel)
            .where(
                LoginAttemptModel.email == email,
                LoginAttemptModel.occurred_at >= since,
            )
        )
        if self._tenant_id:
            stmt = stmt.where(LoginAttemptModel.tenant_id == self._tenant_id)
        result = await self._db.execute(stmt)
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
                tenant_id=self._tenant_id,
            )
        )

    async def get_locked_until(self, email: str) -> datetime | None:
        stmt = (
            select(LoginAttemptModel.locked_until)
            .where(
                LoginAttemptModel.email == email,
                LoginAttemptModel.locked_until.is_not(None),
            )
            .order_by(LoginAttemptModel.locked_until.desc())
            .limit(1)
        )
        if self._tenant_id:
            stmt = stmt.where(LoginAttemptModel.tenant_id == self._tenant_id)
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()

    async def clear(self, email: str) -> None:
        stmt = delete(LoginAttemptModel).where(LoginAttemptModel.email == email)
        if self._tenant_id:
            stmt = stmt.where(LoginAttemptModel.tenant_id == self._tenant_id)
        await self._db.execute(stmt)
