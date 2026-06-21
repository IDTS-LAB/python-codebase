from uuid import UUID

from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.database.model import Base


class UserHasRoleModel(Base):
    __tablename__ = "user_has_roles"
    __table_args__ = (
        UniqueConstraint("user_id", "role_id", name="uq_user_has_roles_user_id_role_id"),
    )

    user_id: Mapped[UUID] = mapped_column(index=True)
    role_id: Mapped[UUID] = mapped_column(index=True)
