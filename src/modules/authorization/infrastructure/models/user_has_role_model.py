from uuid import UUID

from sqlalchemy import Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.modules.user.infrastructure.models.user_model import UserModel
from src.shared.database.model import Base


class UserHasRoleModel(Base):
    """Junction table for user-to-role assignments.

    Many-to-many relationship between users and roles.
    Supports RBAC by linking users to their assigned roles.
    """

    __tablename__ = "user_has_roles"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "role_id", name="uq_user_has_roles_user_id_role_id"
        ),
        Index("ix_user_has_roles_user_id", "user_id"),
        Index("ix_user_has_roles_role_id", "role_id"),
    )

    user_id: Mapped[UUID] = mapped_column(nullable=False)
    role_id: Mapped[UUID] = mapped_column(nullable=False)

    # Relationships
    user: Mapped["UserModel"] = relationship(
        back_populates="role_assignments",
        foreign_keys=[user_id],
    )
    role: Mapped["RoleModel"] = relationship(
        back_populates="user_assignments",
        foreign_keys=[role_id],
    )
