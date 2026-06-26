from uuid import uuid4

from sqlalchemy import select

from src.core.config.setting import get_settings
from src.core.database.postgres.session import AsyncSessionLocal
from src.core.middleware.tenant import set_default_tenant_id
from src.modules.tenants.infrastructure.models.tenant_model import TenantModel

DEFAULT_TENANT_SLUG = "default"


async def seed_default_tenant() -> None:
    settings = get_settings()
    if settings.MULTITENANT_ENABLED:
        return

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(TenantModel).where(TenantModel.slug == DEFAULT_TENANT_SLUG)
        )
        existing = result.scalar_one_or_none()
        if existing:
            set_default_tenant_id(existing.id)
            return

        tenant = TenantModel(
            id=uuid4(),
            name="Default Tenant",
            slug=DEFAULT_TENANT_SLUG,
            domain=None,
        )
        session.add(tenant)
        await session.commit()
        await session.refresh(tenant)
        set_default_tenant_id(tenant.id)
