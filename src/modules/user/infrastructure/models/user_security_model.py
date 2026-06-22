from datetime import datetime

from sqlalchemy import String, Boolean, DateTime, Integer, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.shared.database.mixin.timestamp import SoftDeleteMixin, TimeStampMixin
from src.shared.database.model import Base


class UserSecurityModel(Base, TimeStampMixin, SoftDeleteMixin):
    """User security configuration and state.
    
    One-to-one relationship with users table.
    Contains sensitive security-related fields separated from core identity.
    """
    __tablename__ = "user_security"
    __table_args__ = (
        Index("ix_user_security_user_id", "user_id", unique=True),
        Index("ix_user_security_locked_until", "locked_until"),
        Index("ix_user_security_two_factor_enabled", "two_factor_enabled"),
    )

    user_id: Mapped[str] = mapped_column(
        String(36),  # UUID as string for FK
        unique=True,
        nullable=False,
    )
    
    # Login Attempt Tracking
    failed_login_attempts: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    
    # Account Lockout
    locked_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    
    # Password Management
    password_changed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    
    # Two-Factor Authentication
    two_factor_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    two_factor_secret: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    two_factor_backup_codes: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
    )
    
    # Relationship
    user: Mapped["UserModel"] = relationship(
        back_populates="security",
        foreign_keys=[user_id],
    )
