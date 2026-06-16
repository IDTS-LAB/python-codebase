from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database.session import get_db
from src.modules.user.infrastructure.repositories.user_repository import (
    SQLAlchemyUserRepository,
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_db_session(db: AsyncSession = Depends(get_db)) -> AsyncSession:
    return db


async def get_current_user(
    request: Request,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    1. 'token' is extracted by oauth2_scheme (for Swagger docs).
    2. 'request.state.user_id' was already validated and set by our Auth Middleware.
    3. We fetch the full user object from the DB for downstream use.
    """
    user_id = getattr(request.state, "user_id", None)

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated. Token invalid or missing.",
        )

    repo = SQLAlchemyUserRepository(db)
    user = await repo.get_by_id(UUID(user_id))

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Authenticated user not found in database",
        )

    return {
        "id": user.id,
        "email": user.email,
        "raw_payload": getattr(request.state, "token_payload", {}),
    }
