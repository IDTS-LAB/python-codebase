from uuid import UUID

from sqlalchemy import Date, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.modules.user.infrastructure.models.user_model import UserModel
from src.shared.database.mixin.tenant import TenantMixin
from src.shared.database.mixin.timestamp import SoftDeleteMixin, TimeStampMixin
from src.shared.database.model import Base


class UserProfileModel(Base, TimeStampMixin, SoftDeleteMixin, TenantMixin):
    """User profile containing personal information.

    One-to-one relationship with users table.
    Contains fields that are not required for authentication.
    """

    __tablename__ = "user_profiles"
    __table_args__ = (Index("ix_user_profiles_user_id", "user_id", unique=True),)

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id"),
        unique=True,
        nullable=False,
    )

    # Personal Information
    first_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Avatar and Bio
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Birth Date
    birth_date: Mapped[Date | None] = mapped_column(Date, nullable=True)

    # Relationship
    user: Mapped["UserModel"] = relationship(
        back_populates="profile",
        foreign_keys=[user_id],
    )
