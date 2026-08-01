from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column


class TenantMixin:
    tenant_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("tenants.id"),
        nullable=False,
        sort_order=-60,
    )
