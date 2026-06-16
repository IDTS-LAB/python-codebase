from datetime import UTC, datetime

from sqlalchemy import DateTime, Null
from sqlalchemy.orm import Mapped, mapped_column


class TimeStampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now(UTC), onupdate=datetime.now(UTC)
    )


class SoftDeleteMixin:
    deleted_at: Mapped[datetime] = mapped_column(DateTime, default=Null, nullable=True)

    def soft_delete(self):
        self.soft_delete = datetime.now(UTC)
