"""Handlers for two-factor authentication operations."""

from src.core.email.service import EmailService
from src.modules.user.application.auth.two_factor.command import (
    DisableTOTPCommand,
    RegenerateBackupCodesCommand,
    SendEmail2FACodeCommand,
    SetupTOTPCommand,
    Verify2FACommand,
    VerifyEmail2FACodeCommand,
    VerifyTOTPSetupCommand,
)
from src.modules.user.domain.repositories.user_repository import UserRepository
from src.shared.unit_of_work import UnitOfWork


class SetupTOTPHandler:
    """Handler for setting up TOTP 2FA."""

    def __init__(
        self,
        user_repository: UserRepository,
        unit_of_work: UnitOfWork,
    ):
        self._user_repository = user_repository
        self._unit_of_work = unit_of_work

    async def execute(self, command: SetupTOTPCommand) -> dict[str, str]:
        from src.core.security.two_factor_auth import TwoFactorAuthService

        service = TwoFactorAuthService(
            user_repository=self._user_repository,
            unit_of_work=self._unit_of_work,
        )
        return await service.setup_totp(command.user_id)


class VerifyTOTPSetupHandler:
    """Handler for verifying and enabling TOTP 2FA."""

    def __init__(
        self,
        user_repository: UserRepository,
        unit_of_work: UnitOfWork,
    ):
        self._user_repository = user_repository
        self._unit_of_work = unit_of_work

    async def execute(
        self, command: VerifyTOTPSetupCommand
    ) -> dict[str, list[str]]:
        from src.core.security.two_factor_auth import TwoFactorAuthService

        service = TwoFactorAuthService(
            user_repository=self._user_repository,
            unit_of_work=self._unit_of_work,
        )
        return await service.verify_totp_setup(command.user_id, command.code)


class DisableTOTPHandler:
    """Handler for disabling TOTP 2FA."""

    def __init__(
        self,
        user_repository: UserRepository,
        unit_of_work: UnitOfWork,
    ):
        self._user_repository = user_repository
        self._unit_of_work = unit_of_work

    async def execute(self, command: DisableTOTPCommand) -> bool:
        from src.core.security.two_factor_auth import TwoFactorAuthService

        service = TwoFactorAuthService(
            user_repository=self._user_repository,
            unit_of_work=self._unit_of_work,
        )
        return await service.disable_totp(command.user_id, command.code)


class SendEmail2FACodeHandler:
    """Handler for sending email-based 2FA codes."""

    def __init__(
        self,
        user_repository: UserRepository,
        unit_of_work: UnitOfWork,
        email_service: EmailService | None = None,
    ):
        self._user_repository = user_repository
        self._unit_of_work = unit_of_work
        self._email_service = email_service

    async def execute(self, command: SendEmail2FACodeCommand) -> bool:
        from src.core.security.two_factor_auth import TwoFactorAuthService

        service = TwoFactorAuthService(
            user_repository=self._user_repository,
            unit_of_work=self._unit_of_work,
            email_service=self._email_service,
        )
        return await service.send_email_2fa_code(command.user_id)


class VerifyEmail2FACodeHandler:
    """Handler for verifying email-based 2FA codes."""

    def __init__(
        self,
        user_repository: UserRepository,
        unit_of_work: UnitOfWork,
    ):
        self._user_repository = user_repository
        self._unit_of_work = unit_of_work

    async def execute(self, command: VerifyEmail2FACodeCommand) -> bool:
        from src.core.security.two_factor_auth import TwoFactorAuthService

        service = TwoFactorAuthService(
            user_repository=self._user_repository,
            unit_of_work=self._unit_of_work,
        )
        return await service.verify_email_2fa_code(command.user_id, command.code)


class RegenerateBackupCodesHandler:
    """Handler for regenerating backup codes."""

    def __init__(
        self,
        user_repository: UserRepository,
        unit_of_work: UnitOfWork,
    ):
        self._user_repository = user_repository
        self._unit_of_work = unit_of_work

    async def execute(
        self, command: RegenerateBackupCodesCommand
    ) -> dict[str, list[str]]:
        from src.core.security.two_factor_auth import TwoFactorAuthService

        service = TwoFactorAuthService(
            user_repository=self._user_repository,
            unit_of_work=self._unit_of_work,
        )
        return await service.regenerate_backup_codes(
            command.user_id, command.verify_code
        )


class Verify2FAHandler:
    """Handler for verifying 2FA codes during login."""

    def __init__(
        self,
        user_repository: UserRepository,
        unit_of_work: UnitOfWork,
    ):
        self._user_repository = user_repository
        self._unit_of_work = unit_of_work

    async def execute(self, command: Verify2FACommand) -> bool:
        from src.core.security.two_factor_auth import TwoFactorAuthService

        user = await self._user_repository.get_by_id_with_relations(command.user_id)
        if not user:
            raise ValueError("User not found")

        service = TwoFactorAuthService(
            user_repository=self._user_repository,
            unit_of_work=self._unit_of_work,
        )
        return await service.verify_2fa_code(
            user=user,
            code=command.code,
            method=command.method,
        )
