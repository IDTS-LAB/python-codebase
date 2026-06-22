from enum import Enum

from sqlalchemy import String, Boolean, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.shared.database.mixin.timestamp import SoftDeleteMixin, TimeStampMixin
from src.shared.database.model import Base


class ContactType(str, Enum):
    EMAIL = "email"
    PHONE = "phone"
    MOBILE = "mobile"
    WORK_PHONE = "work_phone"
    HOME_PHONE = "home_phone"
    OTHER = "other"


class UserContactModel(Base, TimeStampMixin, SoftDeleteMixin):
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

    user_id: Mapped[str] = mapped_column(
        String(36),  # UUID as string for FK
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
