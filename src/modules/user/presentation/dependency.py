from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database.postgres.session import get_db, get_unit_of_work
from src.core.dependency.tenant import get_current_tenant_id
from src.core.email.factory import create_email_service
from src.core.email.service import EmailService
from src.core.security.account_lockout import AccountLockoutService
from src.core.security.audit import AuditService
from src.core.security.infrastructure.repositories.audit_log_repository import (
    SQLAlchemyAuditRepository,
)
from src.core.security.infrastructure.repositories.login_attempt_repository import (
    SQLAlchemyLoginAttemptRepository,
)
from src.core.security.token_revocation import TokenRevocationService
from src.modules.authorization.domain.services.authorization_service import (
    AuthorizationService,
)
from src.modules.authorization.presentation.dependency import get_authorization_service
from src.modules.user.application.auth.login_user.handler import LoginUserCommandHandler
from src.modules.user.application.auth.logout_user.handler import (
    LogoutUserCommandHandler,
)
from src.modules.user.application.auth.refresh_token.handler import (
    RefreshTokenCommandHandler,
)
from src.modules.user.application.auth.register_user.handler import (
    RegisterUserCommandHandler,
)
from src.modules.user.application.auth.two_factor.handler import (
    DisableTOTPHandler,
    RegenerateBackupCodesHandler,
    SendEmail2FACodeHandler,
    SetupTOTPHandler,
    Verify2FAHandler,
    VerifyEmail2FACodeHandler,
    VerifyTOTPSetupHandler,
)
from src.modules.user.application.detail_user.handler import DetailUserQueryHandler
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


def get_user_repository(
    db: AsyncSession = Depends(get_db),
    tenant_id: int = Depends(get_current_tenant_id),
) -> UserRepository:
    return SQLAlchemyUserRepository(db, tenant_id)


def get_email_service() -> EmailService:
    return create_email_service()


def get_refresh_token_repository(
    db: AsyncSession = Depends(get_db),
    tenant_id: int = Depends(get_current_tenant_id),
) -> RefreshTokenRepository:
    return SQLAlchemyRefreshTokenRepository(db, tenant_id)


def get_token_revocation_service() -> TokenRevocationService:
    return TokenRevocationService()


def get_audit_service(
    db: AsyncSession = Depends(get_db),
    tenant_id: int = Depends(get_current_tenant_id),
) -> AuditService:
    return AuditService(SQLAlchemyAuditRepository(db, tenant_id))


def get_account_lockout_service(
    db: AsyncSession = Depends(get_db),
    tenant_id: int = Depends(get_current_tenant_id),
) -> AccountLockoutService:
    return AccountLockoutService(SQLAlchemyLoginAttemptRepository(db, tenant_id))


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
    account_lockout_service: AccountLockoutService = Depends(
        get_account_lockout_service
    ),
    audit_service: AuditService = Depends(get_audit_service),
) -> LoginUserCommandHandler:
    return LoginUserCommandHandler(
        user_repo,
        refresh_token_repo,
        unit_of_work,
        account_lockout_service,
        audit_service,
    )


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
    token_revocation_service: TokenRevocationService = Depends(
        get_token_revocation_service
    ),
) -> LogoutUserCommandHandler:
    return LogoutUserCommandHandler(
        refresh_token_repo,
        unit_of_work,
        token_revocation_service,
    )


# Two-Factor Authentication Handlers


def get_setup_totp_handler(
    user_repo: UserRepository = Depends(get_user_repository),
    unit_of_work: UnitOfWork = Depends(get_unit_of_work),
) -> SetupTOTPHandler:
    return SetupTOTPHandler(user_repo, unit_of_work)


def get_verify_totp_setup_handler(
    user_repo: UserRepository = Depends(get_user_repository),
    unit_of_work: UnitOfWork = Depends(get_unit_of_work),
) -> VerifyTOTPSetupHandler:
    return VerifyTOTPSetupHandler(user_repo, unit_of_work)


def get_disable_totp_handler(
    user_repo: UserRepository = Depends(get_user_repository),
    unit_of_work: UnitOfWork = Depends(get_unit_of_work),
) -> DisableTOTPHandler:
    return DisableTOTPHandler(user_repo, unit_of_work)


def get_send_email_2fa_code_handler(
    user_repo: UserRepository = Depends(get_user_repository),
    unit_of_work: UnitOfWork = Depends(get_unit_of_work),
    email_service=Depends(get_email_service),
) -> SendEmail2FACodeHandler:
    return SendEmail2FACodeHandler(user_repo, unit_of_work, email_service)


def get_verify_email_2fa_code_handler(
    user_repo: UserRepository = Depends(get_user_repository),
    unit_of_work: UnitOfWork = Depends(get_unit_of_work),
) -> VerifyEmail2FACodeHandler:
    return VerifyEmail2FACodeHandler(user_repo, unit_of_work)


def get_regenerate_backup_codes_handler(
    user_repo: UserRepository = Depends(get_user_repository),
    unit_of_work: UnitOfWork = Depends(get_unit_of_work),
) -> RegenerateBackupCodesHandler:
    return RegenerateBackupCodesHandler(user_repo, unit_of_work)


def get_verify_2fa_handler(
    user_repo: UserRepository = Depends(get_user_repository),
    unit_of_work: UnitOfWork = Depends(get_unit_of_work),
) -> Verify2FAHandler:
    return Verify2FAHandler(user_repo, unit_of_work)
