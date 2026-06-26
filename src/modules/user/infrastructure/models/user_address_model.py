from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.modules.user.infrastructure.models.user_model import UserModel
from src.shared.database.mixin.tenant import TenantMixin
from src.shared.database.mixin.timestamp import SoftDeleteMixin, TimeStampMixin
from src.shared.database.model import Base


class UserAddressModel(Base, TimeStampMixin, SoftDeleteMixin, TenantMixin):
    """User addresses supporting multiple locations.

    One-to-many relationship with users table.
    Supports home, billing, shipping, and custom address labels.
    """

    __tablename__ = "user_addresses"
    __table_args__ = (
        Index("ix_user_addresses_user_id", "user_id"),
        Index("ix_user_addresses_label", "label"),
        Index("ix_user_addresses_is_default", "is_default"),
        Index("ix_user_addresses_country", "country"),
    )

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )

    # Address Label (home, billing, shipping, work, etc.)
    label: Mapped[str] = mapped_column(String(100), nullable=False)

    # Address Lines
    line1: Mapped[str] = mapped_column(String(255), nullable=False)
    line2: Mapped[str | None] = mapped_column(String(255), nullable=True)
    line3: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # City and State
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    state: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Postal Code
    postal_code: Mapped[str] = mapped_column(String(20), nullable=False)

    # Country (ISO 3166-1 alpha-2)
    country: Mapped[str] = mapped_column(String(2), nullable=False)

    # Flags
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationship
    user: Mapped["UserModel"] = relationship(
        back_populates="addresses",
        foreign_keys=[user_id],
    )
