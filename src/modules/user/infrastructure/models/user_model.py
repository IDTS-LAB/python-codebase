from enum import Enum

from sqlalchemy import Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.modules.authorization.infrastructure.models.user_has_role_model import (
    UserHasRoleModel,
)
from src.modules.user.infrastructure.models.refresh_token_model import UserSessionModel
from src.modules.user.infrastructure.models.user_address_model import UserAddressModel
from src.modules.user.infrastructure.models.user_contact_model import UserContactModel
from src.modules.user.infrastructure.models.user_profile_model import UserProfileModel
from src.modules.user.infrastructure.models.user_security_model import UserSecurityModel
from src.modules.user.infrastructure.models.user_settings_model import UserSettingsModel
from src.modules.user.infrastructure.models.user_verification_model import (
    UserVerificationModel,
)
from src.shared.database.mixin.timestamp import SoftDeleteMixin, TimeStampMixin
from src.shared.database.model import Base


class UserStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING_VERIFICATION = "pending_verification"


class AuthProvider(str, Enum):
    LOCAL = "local"
    GOOGLE = "google"
    GITHUB = "github"
    MICROSOFT = "microsoft"
    SSO = "sso"


class UserModel(
    Base,
    TimeStampMixin,
    SoftDeleteMixin,
):
    """Core user identity and authentication table.

    Contains only identity and authentication related fields.
    All other user data is in separate normalized tables.
    """

    __tablename__ = "users"
    __table_args__ = (
        Index("ix_users_status", "status"),
        Index("ix_users_auth_provider", "auth_provider"),
    )

    # Identity
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    username: Mapped[str | None] = mapped_column(
        String(100), unique=True, index=True, nullable=True
    )

    # Authentication
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    auth_provider: Mapped[str] = mapped_column(
        String(50), default=AuthProvider.LOCAL, nullable=False
    )
    external_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Status
    status: Mapped[str] = mapped_column(
        String(50), default=UserStatus.PENDING_VERIFICATION, nullable=False
    )

    # Relationships (one-to-one)
    profile: Mapped["UserProfileModel"] = relationship(
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    security: Mapped["UserSecurityModel"] = relationship(
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    settings: Mapped["UserSettingsModel"] = relationship(
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )

    # Relationships (one-to-many)
    contacts: Mapped[list["UserContactModel"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    addresses: Mapped[list["UserAddressModel"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    verifications: Mapped[list["UserVerificationModel"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    sessions: Mapped[list["UserSessionModel"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    role_assignments: Mapped[list["UserHasRoleModel"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
