from enum import Enum
from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.modules.user.infrastructure.models.user_model import UserModel
from src.shared.database.mixin.tenant import TenantMixin
from src.shared.database.mixin.timestamp import SoftDeleteMixin, TimeStampMixin
from src.shared.database.model import Base


class ContactType(str, Enum):
    EMAIL = "email"
    PHONE = "phone"
    MOBILE = "mobile"
    WORK_PHONE = "work_phone"
    HOME_PHONE = "home_phone"
    OTHER = "other"


class UserContactModel(Base, TimeStampMixin, SoftDeleteMixin, TenantMixin):
    """User contact methods supporting multiple channels.

    One-to-many relationship with users table.
    Allows users to have multiple contact methods (phones, alternate emails).
    """

    __tablename__ = "user_contacts"
    __table_args__ = (
        Index("ix_user_contacts_user_id", "user_id"),
        Index("ix_user_contacts_type", "contact_type"),
        Index("ix_user_contacts_is_primary", "is_primary"),
    )

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )

    # Contact Information
    contact_type: Mapped[str] = mapped_column(String(50), nullable=False)
    value: Mapped[str] = mapped_column(String(255), nullable=False)

    # Flags
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationship
    user: Mapped["UserModel"] = relationship(
        back_populates="contacts",
        foreign_keys=[user_id],
    )
