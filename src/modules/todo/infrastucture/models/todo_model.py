import uuid

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.database.model import Base
from src.shared.database.mixin.timestamp import SoftDeleteMixin, TimeStampMixin


class TodoModel(Base, TimeStampMixin, SoftDeleteMixin):
    __tablename__ = "todos"

    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
