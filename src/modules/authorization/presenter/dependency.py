from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.authorization.infrastructure.repositories.casbin_policy_repository import (
    SQLAlchemyCasbinPolicyRepository,
)
from src.core.authorization.infrastructure.services.casbin_authorization_service import (
    CasbinAuthorizationService,
)
from src.core.database.postgres.session import get_db


def get_casbin_policy_repository(
    db: AsyncSession = Depends(get_db),
) -> SQLAlchemyCasbinPolicyRepository:
    return SQLAlchemyCasbinPolicyRepository(db=db)


def get_casbin_authorization_service(
    repository: SQLAlchemyCasbinPolicyRepository = Depends(
        get_casbin_policy_repository
    ),
) -> CasbinAuthorizationService:
    return CasbinAuthorizationService(repository)
