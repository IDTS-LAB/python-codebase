from sqlalchemy import String, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.shared.database.mixin.timestamp import SoftDeleteMixin, TimeStampMixin
from src.shared.database.model import Base


class RoleModel(Base, TimeStampMixin, SoftDeleteMixin):
    """Role definition for RBAC system.
    
    Roles group permissions and can be assigned to users.
    """
    __tablename__ = "roles"
    __table_args__ = (
        Index("ix_roles_name", "name", unique=True),
    )

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    # Relationships
    permissions: Mapped[list["RolePermissionModel"]] = relationship(
        back_populates="role",
        cascade="all, delete-orphan",
    )
    user_assignments: Mapped[list["UserHasRoleModel"]] = relationship(
        back_populates="role",
        cascade="all, delete-orphan",
    )
