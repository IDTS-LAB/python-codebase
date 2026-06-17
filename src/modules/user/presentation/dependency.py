from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.authorization.dependencies import get_authorization_service
from src.core.authorization.domain.service import AuthorizationService
from src.core.database.session import get_db, get_unit_of_work
from src.modules.user.application.detail_user.handler import DetailUserQueryHandler
from src.modules.user.application.login_user.handler import LoginUserCommandHandler
from src.modules.user.application.logout_user.handler import LogoutUserCommandHandler
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
from src.shared.unit_of_work import UnitOfWork


def get_user_repository(db: AsyncSession = Depends(get_db)) -> UserRepository:
    return SQLAlchemyUserRepository(db)


def get_refresh_token_repository(
    db: AsyncSession = Depends(get_db),
) -> RefreshTokenRepository:
    return SQLAlchemyRefreshTokenRepository(db)


def get_register_handler(
    repo: UserRepository = Depends(get_user_repository),
    unit_of_work: UnitOfWork = Depends(get_unit_of_work),
    authorization_service: AuthorizationService = Depends(get_authorization_service),
) -> RegisterUserCommandHandler:
    return RegisterUserCommandHandler(repo, unit_of_work, authorization_service)


def get_login_handler(
    user_repo: UserRepository = Depends(get_user_repository),
    refresh_token_repo: RefreshTokenRepository = Depends(get_refresh_token_repository),
    unit_of_work: UnitOfWork = Depends(get_unit_of_work),
) -> LoginUserCommandHandler:
    return LoginUserCommandHandler(user_repo, refresh_token_repo, unit_of_work)


def get_user_detail_handler(
    repo: UserRepository = Depends(get_user_repository),
) -> DetailUserQueryHandler:
    return DetailUserQueryHandler(repo)


def get_refresh_token_handler(
    refresh_token_repo: RefreshTokenRepository = Depends(get_refresh_token_repository),
    unit_of_work: UnitOfWork = Depends(get_unit_of_work),
) -> RefreshTokenCommandHandler:
    return RefreshTokenCommandHandler(refresh_token_repo, unit_of_work)


def get_logout_handler(
    refresh_token_repo: RefreshTokenRepository = Depends(get_refresh_token_repository),
    unit_of_work: UnitOfWork = Depends(get_unit_of_work),
) -> LogoutUserCommandHandler:
    return LogoutUserCommandHandler(refresh_token_repo, unit_of_work)
