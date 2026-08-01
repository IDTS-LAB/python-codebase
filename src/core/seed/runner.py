from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config.setting import get_settings
from src.core.database.postgres.session import AsyncSessionLocal
from src.core.seed.authorization import AuthorizationSeedResult, seed_authorization
from src.core.seed.user import SeedUserConfig, UserSeedResult, seed_user
from src.modules.authorization.infrastructure.repositories.casbin_policy_repository import (
    SQLAlchemyCasbinPolicyRepository,
)
from src.modules.authorization.infrastructure.services.casbin_authorization_service import (
    CasbinAuthorizationService,
)
from src.modules.user.infrastructure.repositories.user_repository import (
    SQLAlchemyUserRepository,
)
from src.modules.tenants.infrastructure.models.tenant_model import TenantModel  # noqa: F401


@dataclass(frozen=True)
class SeedResult:
    authorization: AuthorizationSeedResult
    user: UserSeedResult


async def run_seeders() -> SeedResult:
    async with AsyncSessionLocal() as session:
        try:
            result = await run_seeders_with_session(session)
            await session.commit()
            return result
        except Exception:
            await session.rollback()
            raise


async def run_seeders_with_session(session: AsyncSession) -> SeedResult:
    authorization_repository = SQLAlchemyCasbinPolicyRepository(session)
    authorization = await seed_authorization(authorization_repository)
    user = await seed_user(
        user_repository=SQLAlchemyUserRepository(session),
        authorization_service=CasbinAuthorizationService(authorization_repository),
        config=SeedUserConfig.from_settings(get_settings()),
    )
    return SeedResult(authorization=authorization, user=user)
