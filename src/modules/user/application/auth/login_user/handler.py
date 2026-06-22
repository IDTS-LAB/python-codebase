import hashlib
from datetime import datetime, timedelta, timezone
from typing import Literal

from src.core.config.setting import get_settings
from src.core.security.account_lockout import AccountLockoutService
from src.core.security.audit import AuditEvent, AuditService
from src.core.security.jwt import JWTService
from src.core.security.password import PasswordSerrvice
from src.modules.user.application.auth.login_user.command import LoginUserCommand
from src.modules.user.application.auth.login_user.validation import (
    validate_login_user_command,
)
from src.modules.user.domain.entities.refresh_token import RefreshToken
from src.modules.user.domain.repositories.refresh_token_repository import (
    RefreshTokenRepository,
)
from src.modules.user.domain.repositories.user_repository import UserRepository
from src.shared.exceptions.credential_exception import InvalidCredentialsError
from src.shared.unit_of_work import UnitOfWork

settings = get_settings()


class LoginUserCommandHandler:
    def __init__(
        self,
        user_repository: UserRepository,
        refresh_token_repository: RefreshTokenRepository,
        unit_of_work: UnitOfWork,
        account_lockout_service: AccountLockoutService | None = None,
        audit_service: AuditService | None = None,
    ):
        self._user_repository = user_repository
        self._refresh_token_repository = refresh_token_repository
        self._unit_of_work = unit_of_work
        self._account_lockout_service = account_lockout_service
        self._audit_service = audit_service

    async def execute(
        self,
        command: LoginUserCommand,
        two_factor_code: str | None = None,
        two_factor_method: Literal["totp", "email", "backup"] | None = None,
    ) -> dict[str, str]:
        validate_login_user_command(command)

        if self._account_lockout_service is not None:
            try:
                await self._account_lockout_service.ensure_login_allowed(
                    command.username
                )
            except ValueError:
                async with self._unit_of_work:
                    await self._audit_login(command.username, "locked")
                    await self._unit_of_work.commit()
                raise InvalidCredentialsError("Account is temporarily locked")

        user = await self._user_repository.get_by_email(command.username)
        if user is None:
            await self._record_failed_login(command.username)
            raise InvalidCredentialsError("Incorrect email or password")

        if not user or not PasswordSerrvice.verify_password(
            command.password, user.password_hash
        ):
            await self._record_failed_login(command.username)
            raise InvalidCredentialsError("Incorrect email or password")

        # Check if 2FA is enabled and requires verification
        if user.security and user.security.two_factor_enabled:
            if not two_factor_code:
                # Return a temporary token indicating 2FA is required
                temp_token = JWTService.create_access_token(
                    data={"sub": str(user.id), "2fa_required": True},
                    expires_delta=timedelta(minutes=5),
                )
                return {
                    "access_token": temp_token,
                    "refresh_token": "",
                    "2fa_required": True,
                }

            # Verify 2FA code
            from src.core.security.two_factor_auth import TwoFactorAuthService

            two_factor_service = TwoFactorAuthService(
                user_repository=self._user_repository,
                unit_of_work=self._unit_of_work,
            )

            verified = await two_factor_service.verify_2fa_code(
                user=user,
                code=two_factor_code,
                method=two_factor_method or "totp",
            )

            if not verified:
                await self._record_failed_login(command.username)
                raise InvalidCredentialsError("Invalid 2FA code")

        access_token = JWTService.create_access_token(data={"sub": str(user.id)})

        refresh_token_str = JWTService.create_refresh_token(data={"sub": str(user.id)})
        token_hash = hashlib.sha256(refresh_token_str.encode()).hexdigest()
        expires_at = datetime.now(timezone.utc) + timedelta(
            minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES
        )

        async with self._unit_of_work:
            if self._account_lockout_service is not None:
                await self._account_lockout_service.record_successful_login(
                    command.username
                )

            new_rt = RefreshToken.create(
                user_id=user.id, token_hash=token_hash, expires_at=expires_at
            )
            await self._refresh_token_repository.save(new_rt)
            await self._audit_login(command.username, "success", actor_id=str(user.id))
            await self._unit_of_work.commit()

        return {
            "access_token": access_token,
            "refresh_token": refresh_token_str,
        }

    async def _record_failed_login(self, email: str) -> None:
        async with self._unit_of_work:
            if self._account_lockout_service is not None:
                await self._account_lockout_service.record_failed_login(email)
            await self._audit_login(email, "failure")
            await self._unit_of_work.commit()

    async def _audit_login(
        self,
        email: str,
        result: str,
        actor_id: str | None = None,
    ) -> None:
        if self._audit_service is None:
            return
        await self._audit_service.record(
            AuditEvent(
                action="user.login",
                actor_id=actor_id,
                resource_type="user",
                resource_id=actor_id,
                metadata={"email": email, "result": result},
            )
        )
