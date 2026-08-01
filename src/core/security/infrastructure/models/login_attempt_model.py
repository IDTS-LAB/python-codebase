from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.database.mixin.tenant import TenantMixin
from src.shared.database.model import Base


class LoginAttemptModel(Base, TenantMixin):
    __tablename__ = "login_attempts"

    email: Mapped[str] = mapped_column(String(255), index=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    locked_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        index=True,
        nullable=True,
    )
