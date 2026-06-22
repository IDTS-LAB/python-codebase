from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.modules.user.infrastructure.models.user_model import UserModel
from src.shared.database.mixin.timestamp import SoftDeleteMixin, TimeStampMixin
from src.shared.database.model import Base


class UserVerificationModel(Base, TimeStampMixin, SoftDeleteMixin):
    """User verification status per communication channel.

    One-to-many relationship with users table.
    Tracks verification status for email, phone, and other channels.
    """

    __tablename__ = "user_verifications"
    __table_args__ = (
        Index("ix_user_verifications_user_id", "user_id"),
        Index("ix_user_verifications_channel", "channel"),
        Index("ix_user_verifications_is_verified", "is_verified"),
        Index("ix_user_verifications_token", "verification_token"),
    )

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)

    # Verification Channel (email, phone, etc.)
    channel: Mapped[str] = mapped_column(String(50), nullable=False)

    # Verification Status
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Verification Token (for pending verifications)
    verification_token: Mapped[str | None] = mapped_column(String(255), nullable=True)
    token_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationship
    user: Mapped["UserModel"] = relationship(
        back_populates="verifications",
        foreign_keys=[user_id],
    )
