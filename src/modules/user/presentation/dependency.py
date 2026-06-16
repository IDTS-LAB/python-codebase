from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database.session import get_db
from src.modules.user.application.detail_user.handler import DetailUserQueryHandler
from src.modules.user.application.login_user.handler import LoginUserCommandHandler
from src.modules.user.application.refresh_token.handler import (
    RefreshTokenCommandHandler,
)
from src.modules.user.application.register_user.handler import (
    RegisterUserCommandHandler,
)
from src.modules.user.domain.repositories.refresh_token_repository import (
    RefreshTokenRepository,
)
from src.modules.user.domain.repositories.user_repository import UserRepository
from src.modules.user.infrastructure.repositories.refresh_token_repository import (
    SQLAlchemyRefreshTokenRepository,
)
from src.modules.user.infrastructure.repositories.user_repository import (
    SQLAlchemyUserRepository,
)


def get_user_repository(db: AsyncSession = Depends(get_db)) -> UserRepository:
    return SQLAlchemyUserRepository(db)


def get_refresh_token_repository(
    db: AsyncSession = Depends(get_db),
) -> RefreshTokenRepository:
    return SQLAlchemyRefreshTokenRepository(db)


def get_register_handler(
    repo: UserRepository = Depends(get_user_repository),
) -> RegisterUserCommandHandler:
    return RegisterUserCommandHandler(repo)


def get_login_handler(
    user_repo: UserRepository = Depends(get_user_repository),
    refresh_token_repo: RefreshTokenRepository = Depends(get_refresh_token_repository),
) -> LoginUserCommandHandler:
    return LoginUserCommandHandler(user_repo, refresh_token_repo)


def get_user_detail_handler(
    repo: UserRepository = Depends(get_user_repository),
) -> DetailUserQueryHandler:
    return DetailUserQueryHandler(repo)


def get_refresh_token_handler(
    refresh_token_repo: RefreshTokenRepository = Depends(get_refresh_token_repository),
) -> RefreshTokenCommandHandler:
    return RefreshTokenCommandHandler(refresh_token_repo)
