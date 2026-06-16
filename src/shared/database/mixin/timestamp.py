from datetime import UTC, datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import Mapped, mapped_column


class TimeStampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        sort_order=-90,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        sort_order=-80,
    )


class SoftDeleteMixin:
    deleted_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=True,
        sort_order=-70,
    )

    def soft_delete(self):
        self.deleted_at = datetime.now(UTC)
