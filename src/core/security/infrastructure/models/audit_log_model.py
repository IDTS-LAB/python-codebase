from datetime import datetime

from sqlalchemy import DateTime, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.database.mixin.tenant import TenantMixin
from src.shared.database.model import Base


class AuditLogModel(Base, TenantMixin):
    __tablename__ = "audit_logs"

    action: Mapped[str] = mapped_column(String(120), index=True)
    actor_id: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    resource_type: Mapped[str | None] = mapped_column(String(80), nullable=True)
    resource_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    request_id: Mapped[str | None] = mapped_column(String(120), index=True, nullable=True)
    meta: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
