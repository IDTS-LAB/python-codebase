from datetime import datetime

from sqlalchemy import DateTime, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.database.mixin.tenant import TenantMixin
from src.shared.database.model import Base


class ErrorTraceModel(Base, TenantMixin):
    __tablename__ = "error_traces"

    error_type: Mapped[str] = mapped_column(String(120), index=True)
    message: Mapped[str] = mapped_column(Text)
    traceback: Mapped[str] = mapped_column(Text)
    method: Mapped[str] = mapped_column(String(12))
    path: Mapped[str] = mapped_column(String(500), index=True)
    actor_id: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    request_id: Mapped[str | None] = mapped_column(String(120), index=True, nullable=True)
    meta: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
