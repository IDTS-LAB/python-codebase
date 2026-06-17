from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.database.model import Base


class RoleModel(Base):
    __tablename__ = "roles"

    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
