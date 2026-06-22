from uuid import UUID

from sqlalchemy import ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.shared.database.model import Base


class RolePermissionModel(Base):
    """Junction table for role-to-permission assignments.

    Many-to-many relationship between roles and permissions.
    """

    __tablename__ = "role_permissions"
    __table_args__ = (
        UniqueConstraint(
            "role_id",
            "permission_id",
            name="uq_role_permissions_role_id_permission_id",
        ),
        Index("ix_role_permissions_role_id", "role_id"),
        Index("ix_role_permissions_permission_id", "permission_id"),
    )

    role_id: Mapped[UUID] = mapped_column(ForeignKey("roles.id"), nullable=False)
    permission_id: Mapped[UUID] = mapped_column(
        ForeignKey("permissions.id"),
        nullable=False,
    )

    # Relationships
    role: Mapped["RoleModel"] = relationship(  # type: ignore[name-defined]
        back_populates="permissions",
        foreign_keys=[role_id],
    )
    permission: Mapped["PermissionModel"] = relationship(  # type: ignore[name-defined]
        back_populates="roles",
        foreign_keys=[permission_id],
    )
