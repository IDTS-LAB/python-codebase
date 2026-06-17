from collections.abc import Callable

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.authorization.domain.service import AuthorizationService
from src.core.authorization.infrastructure.repositories.casbin_policy_repository import (
    SQLAlchemyCasbinPolicyRepository,
)
from src.core.authorization.infrastructure.services.casbin_authorization_service import (
    CasbinAuthorizationService,
)
from src.core.database.postgres.session import get_db
from src.core.dependency.auth import get_current_user


def get_authorization_service(
    db: AsyncSession = Depends(get_db),
) -> AuthorizationService:
    return CasbinAuthorizationService(SQLAlchemyCasbinPolicyRepository(db))


def require_permission(resource: str, action: str) -> Callable:
    async def dependency(
        current_user: dict = Depends(get_current_user),
        authorization_service: AuthorizationService = Depends(
            get_authorization_service
        ),
    ) -> dict:
        allowed = await authorization_service.can(
            subject=str(current_user.get("id")),
            resource=resource,
            action=action,
        )
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied",
            )
        return current_user

    return dependency
