from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.database.mixin.tenant import TenantMixin
from src.shared.database.model import Base


class CasbinRuleModel(Base, TenantMixin):
    __tablename__ = "casbin_rules"

    ptype: Mapped[str] = mapped_column(String(16), index=True)
    v0: Mapped[str | None] = mapped_column(String(255), index=True, nullable=True)
    v1: Mapped[str | None] = mapped_column(String(255), index=True, nullable=True)
    v2: Mapped[str | None] = mapped_column(String(255), index=True, nullable=True)
    v3: Mapped[str | None] = mapped_column(String(255), nullable=True)
    v4: Mapped[str | None] = mapped_column(String(255), nullable=True)
    v5: Mapped[str | None] = mapped_column(String(255), nullable=True)
