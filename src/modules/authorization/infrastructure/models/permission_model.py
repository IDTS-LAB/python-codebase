from uuid import UUID

from sqlalchemy import ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.shared.database.mixin.tenant import TenantMixin
from src.shared.database.mixin.timestamp import SoftDeleteMixin, TimeStampMixin
from src.shared.database.model import Base


class PermissionModel(Base, TimeStampMixin, SoftDeleteMixin, TenantMixin):
    """Permission definition for RBAC system.

    Permissions represent specific actions on resources.
    Linked to authorization_resources for resource management.
    """

    __tablename__ = "permissions"
    __table_args__ = (
        UniqueConstraint("resource", "action", name="uq_permissions_resource_action"),
        Index("ix_permissions_key", "key", unique=True),
        Index("ix_permissions_resource", "resource"),
        Index("ix_permissions_action", "action"),
        Index("ix_permissions_resource_id", "resource_id"),
    )

    key: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    resource_id: Mapped[UUID] = mapped_column(
        ForeignKey("authorization_resources.id"),
        nullable=False,
    )
    resource: Mapped[str] = mapped_column(String(100), nullable=False)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Relationships
    roles: Mapped[list["RolePermissionModel"]] = relationship(  # type: ignore[name-defined]
        back_populates="permission",
        cascade="all, delete-orphan",
    )
    authorization_resource: Mapped["AuthorizationResourceModel"] = relationship(  # type: ignore[name-defined]
        back_populates="permissions",
        foreign_keys=[resource_id],
    )
