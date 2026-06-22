from datetime import datetime

from sqlalchemy import Boolean, DateTime, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.shared.database.mixin.timestamp import SoftDeleteMixin, TimeStampMixin
from src.shared.database.model import Base


class UserSessionModel(Base, TimeStampMixin, SoftDeleteMixin):
    """User session management for tracking active sessions.

    One-to-many relationship with users table.
    Stores refresh tokens, device info, and login history.
    """

    __tablename__ = "user_sessions"
    __table_args__ = (
        Index("ix_user_sessions_user_id", "user_id"),
        Index("ix_user_sessions_token_hash", "refresh_token_hash", unique=True),
        Index("ix_user_sessions_expires_at", "expires_at"),
        Index("ix_user_sessions_is_revoked", "is_revoked"),
        Index("ix_user_sessions_device_info", "device_info"),
    )

    user_id: Mapped[str] = mapped_column(
        String(36),  # UUID as string for FK
        nullable=False,
    )

    # Session Token (hashed for security)
    refresh_token_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    # Session Expiry
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    # Device and Location Info
    device_info: Mapped[str | None] = mapped_column(String(500), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(
        String(45), nullable=True
    )  # IPv6 compatible
    user_agent: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    # Session Status
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    revoked_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Relationship
    user: Mapped["UserModel"] = relationship(  # type: ignore[name-defined]
        back_populates="sessions",
        foreign_keys=[user_id],
    )
