from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.tenants.domain.entities.tenant import Tenant
from src.modules.tenants.domain.repositories.tenant_repository import TenantRepository
from src.modules.tenants.infrastructure.models.tenant_model import TenantModel


class SQLAlchemyTenantRepository(TenantRepository):
    def __init__(self, db: AsyncSession):
        self._db = db

    async def get_by_slug(self, slug: str) -> Tenant | None:
        result = await self._db.execute(
            select(TenantModel).where(TenantModel.slug == slug)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_domain(self, domain: str) -> Tenant | None:
        result = await self._db.execute(
            select(TenantModel).where(TenantModel.domain == domain)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_id(self, tenant_id: int) -> Tenant | None:
        result = await self._db.execute(
            select(TenantModel).where(TenantModel.id == tenant_id)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def save(self, tenant: Tenant) -> Tenant:
        existing = None
        if tenant.id:
            existing = await self.get_by_id(tenant.id)

        if existing:
            model = await self._get_model(tenant.id)
            model.name = tenant.name
            model.slug = tenant.slug
            model.domain = tenant.domain
        else:
            model = TenantModel(
                name=tenant.name,
                slug=tenant.slug,
                domain=tenant.domain,
            )
            self._db.add(model)

        await self._db.flush()
        await self._db.refresh(model)
        return self._to_entity(model)

    async def _get_model(self, tenant_id: int) -> TenantModel:
        result = await self._db.execute(
            select(TenantModel).where(TenantModel.id == tenant_id)
        )
        return result.scalar_one()

    def _to_entity(self, model: TenantModel) -> Tenant:
        return Tenant(
            id=model.id,
            name=model.name,
            slug=model.slug,
            domain=model.domain,
        )
