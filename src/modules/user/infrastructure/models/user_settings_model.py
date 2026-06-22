from uuid import UUID

from sqlalchemy import ForeignKey, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.modules.user.infrastructure.models.user_model import UserModel
from src.shared.database.mixin.timestamp import SoftDeleteMixin, TimeStampMixin
from src.shared.database.model import Base


class UserSettingsModel(Base, TimeStampMixin, SoftDeleteMixin):
    """User preferences and settings stored as JSONB.

    One-to-one relationship with users table.
    Flexible schema allows adding new preferences without migrations.

    Example preferences structure:
    {
        "language": "en",
        "timezone": "UTC",
        "theme": "dark",
        "currency": "USD",
        "notifications": {
            "email": true,
            "push": false,
            "sms": false
        },
        "privacy": {
            "profile_visibility": "public",
            "show_email": false
        }
    }
    """

    __tablename__ = "user_settings"
    __table_args__ = (
        Index("ix_user_settings_user_id", "user_id", unique=True),
        Index("ix_user_settings_preferences", "preferences", postgresql_using="gin"),
    )

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id"),
        unique=True,
        nullable=False,
    )

    # Preferences stored as JSONB for flexibility
    preferences: Mapped[dict] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
    )

    # Relationship
    user: Mapped["UserModel"] = relationship(
        back_populates="settings",
        foreign_keys=[user_id],
    )
