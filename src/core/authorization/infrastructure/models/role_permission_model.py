from uuid import UUID

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.database.model import Base


class RolePermissionModel(Base):
    __tablename__ = "role_permissions"
    __table_args__ = (
        UniqueConstraint(
            "role_id",
            "permission_id",
            name="uq_role_permissions_role_id_permission_id",
        ),
    )

    role_id: Mapped[UUID] = mapped_column(ForeignKey("roles.id"), index=True)
    permission_id: Mapped[UUID] = mapped_column(
        ForeignKey("permissions.id"),
        index=True,
    )
