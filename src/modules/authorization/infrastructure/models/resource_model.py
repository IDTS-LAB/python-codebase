from sqlalchemy import String, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.shared.database.mixin.timestamp import SoftDeleteMixin, TimeStampMixin
from src.shared.database.model import Base


class AuthorizationResourceModel(Base, TimeStampMixin, SoftDeleteMixin):
    """Authorization resource definition for grouping permissions.
    
    Resources represent domain entities that permissions act upon.
    Examples: users, todos, documents, reports.
    """
    __tablename__ = "authorization_resources"
    __table_args__ = (
        Index("ix_authorization_resources_key", "key", unique=True),
    )

    key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    # Relationships
    permissions: Mapped[list["PermissionModel"]] = relationship(
        back_populates="authorization_resource",
        cascade="all, delete-orphan",
    )
