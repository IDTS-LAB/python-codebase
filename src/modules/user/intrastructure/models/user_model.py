from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from shared.database.mixin.timestamp import SoftDeleteMixin, TimeStampMixin
from shared.database.model import Base


class UserModel(
    Base,
    TimeStampMixin,
    SoftDeleteMixin,
):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password: Mapped[str] = mapped_column(String(255))
