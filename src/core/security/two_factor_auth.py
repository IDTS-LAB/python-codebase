"""Two-Factor Authentication service supporting TOTP and email-based 2FA."""

from __future__ import annotations

import secrets
from typing import Literal
from uuid import UUID

import pyotp

from src.core.config.setting import get_settings
from src.core.email.service import EmailService
from src.modules.user.domain.entities.user import User
from src.modules.user.domain.repositories.user_repository import UserRepository
from src.shared.unit_of_work import UnitOfWork


class TwoFactorAuthService:
    """Service for managing two-factor authentication.

    Supports:
    - TOTP (Time-based One-Time Password) for authenticator apps like Google Authenticator, Authy, etc.
    - Email-based 2FA codes
    """

    def __init__(
        self,
        user_repository: UserRepository,
        unit_of_work: UnitOfWork,
        email_service: EmailService | None = None,
    ):
        self._user_repository = user_repository
        self._unit_of_work = unit_of_work
        self._email_service = email_service
        self._settings = get_settings()

    async def setup_totp(self, user_id: UUID) -> dict[str, str]:
        """Set up TOTP for a user.

        Returns:
            dict with 'secret', 'uri', and 'qr_code_data' keys
        """
        async with self._unit_of_work:
            user = await self._user_repository.get_by_id_with_relations(user_id)
            if not user or not user.security:
                raise ValueError("User not found")

            # Generate a new secret
            secret = pyotp.random_base32()

            # Create TOTP URI for QR code generation
            issuer = self._settings.JWT_ISSUER or "TodoApp"
            uri = pyotp.totp.TOTP(secret).provisioning_uri(
                name=user.email, issuer_name=issuer
            )

            # Store the secret temporarily (not enabled yet)
            user.security.two_factor_secret = secret
            user.security.two_factor_enabled = False
            await self._user_repository.save_security(user.security)
            await self._unit_of_work.commit()

            return {
                "secret": secret,
                "uri": uri,
                "qr_code_data": f"otpauth://totp/{issuer}:{user.email}?secret={secret}&issuer={issuer}",
            }

    async def verify_totp_setup(self, user_id: UUID, code: str) -> dict[str, list[str]]:
        """Verify TOTP setup and enable 2FA.

        Args:
            user_id: The user's ID
            code: The TOTP code from the authenticator app

        Returns:
            dict with 'backup_codes' key containing recovery codes
        """
        async with self._unit_of_work:
            user = await self._user_repository.get_by_id_with_relations(user_id)
            if not user or not user.security:
                raise ValueError("User not found")

            if not user.security.two_factor_secret:
                raise ValueError("TOTP not set up. Call setup_totp first.")

            # Verify the code
            totp = pyotp.TOTP(user.security.two_factor_secret)
            if not totp.verify(code, valid_window=1):
                raise ValueError("Invalid TOTP code")

            # Generate backup codes
            backup_codes = [secrets.token_hex(4) for _ in range(10)]

            # Enable 2FA and store backup codes
            user.security.two_factor_enabled = True
            user.security.two_factor_backup_codes = ",".join(backup_codes)
            await self._user_repository.save_security(user.security)
            await self._unit_of_work.commit()

            return {"backup_codes": backup_codes}

    async def disable_totp(self, user_id: UUID, code: str) -> bool:
        """Disable TOTP 2FA for a user.

        Args:
            user_id: The user's ID
            code: Current TOTP code or backup code for verification

        Returns:
            True if successfully disabled
        """
        async with self._unit_of_work:
            user = await self._user_repository.get_by_id_with_relations(user_id)
            if not user or not user.security:
                raise ValueError("User not found")

            if not user.security.two_factor_enabled:
                raise ValueError("2FA is not enabled")

            # Verify code
            verified = False

            # Check if it's a backup code
            if user.security.two_factor_backup_codes:
                backup_codes = user.security.two_factor_backup_codes.split(",")
                if code in backup_codes:
                    backup_codes.remove(code)
                    user.security.two_factor_backup_codes = ",".join(backup_codes)
                    verified = True

            # Check if it's a TOTP code
            if not verified and user.security.two_factor_secret:
                totp = pyotp.TOTP(user.security.two_factor_secret)
                if totp.verify(code, valid_window=1):
                    verified = True

            if not verified:
                raise ValueError("Invalid verification code")

            # Disable 2FA
            user.security.two_factor_enabled = False
            user.security.two_factor_secret = None
            user.security.two_factor_backup_codes = None
            await self._user_repository.save_security(user.security)
            await self._unit_of_work.commit()

            return True

    async def send_email_2fa_code(self, user_id: UUID) -> bool:
        """Send a 2FA code via email.

        Args:
            user_id: The user's ID

        Returns:
            True if email was sent successfully
        """
        if self._email_service is None:
            raise ValueError("Email service not configured")

        async with self._unit_of_work:
            user = await self._user_repository.get_by_id_with_relations(user_id)
            if not user:
                raise ValueError("User not found")

            # Generate a 6-digit code
            code = secrets.token_hex(3)[:6]

            # Store the code temporarily in security settings (with expiry info)
            # In production, you'd want to store this in Redis with TTL
            if not user.security:
                raise ValueError("User security not found")

            # Store code with timestamp (format: "code:timestamp")
            import time

            user.security.two_factor_secret = f"email_code:{code}:{int(time.time())}"
            await self._user_repository.save_security(user.security)
            await self._unit_of_work.commit()

            # Send email
            html_body = f"""
            <html>
                <body>
                    <h2>Your Verification Code</h2>
                    <p>Your verification code is: <strong>{code}</strong></p>
                    <p>This code will expire in 10 minutes.</p>
                    <p>If you didn't request this code, please ignore this email.</p>
                </body>
            </html>
            """

            await self._email_service.send_email(
                to=user.email,
                subject="Your Verification Code",
                html_body=html_body,
            )

            return True

    async def verify_email_2fa_code(self, user_id: UUID, code: str) -> bool:
        """Verify an email-based 2FA code.

        Args:
            user_id: The user's ID
            code: The code received via email

        Returns:
            True if code is valid
        """
        async with self._unit_of_work:
            user = await self._user_repository.get_by_id_with_relations(user_id)
            if not user or not user.security:
                raise ValueError("User not found")

            stored = user.security.two_factor_secret
            if not stored or not stored.startswith("email_code:"):
                raise ValueError("No pending email verification code")

            parts = stored.split(":")
            if len(parts) != 3:
                raise ValueError("Invalid code format")

            stored_code = parts[1]
            timestamp = int(parts[2])

            import time

            current_time = int(time.time())

            # Code expires after 10 minutes
            if current_time - timestamp > 600:
                raise ValueError("Code has expired")

            if stored_code != code:
                raise ValueError("Invalid code")

            # Clear the stored code
            user.security.two_factor_secret = None
            await self._user_repository.save_security(user.security)
            await self._unit_of_work.commit()

            return True

    async def verify_2fa_code(
        self, user: User, code: str, method: Literal["totp", "email", "backup"] = "totp"
    ) -> bool:
        """Verify a 2FA code using the specified method.

        Args:
            user: The user entity
            code: The verification code
            method: The verification method ('totp', 'email', or 'backup')

        Returns:
            True if verification successful
        """
        if not user.security:
            raise ValueError("User security not found")

        if method == "totp":
            if (
                not user.security.two_factor_secret
                or not user.security.two_factor_enabled
            ):
                raise ValueError("TOTP 2FA is not enabled")

            totp = pyotp.TOTP(user.security.two_factor_secret)
            return bool(totp.verify(code, valid_window=1))

        elif method == "backup":
            if not user.security.two_factor_backup_codes:
                raise ValueError("No backup codes available")

            backup_codes = user.security.two_factor_backup_codes.split(",")
            if code in backup_codes:
                # Remove used backup code
                backup_codes.remove(code)
                user.security.two_factor_backup_codes = ",".join(backup_codes)
                async with self._unit_of_work:
                    await self._user_repository.save_security(user.security)
                    await self._unit_of_work.commit()
                return True
            return False

        elif method == "email":
            return await self.verify_email_2fa_code(user.id, code)

        return False

    async def regenerate_backup_codes(
        self, user_id: UUID, verify_code: str
    ) -> dict[str, list[str]]:
        """Regenerate backup codes for a user.

        Args:
            user_id: The user's ID
            verify_code: Current TOTP code for verification

        Returns:
            dict with 'backup_codes' key containing new recovery codes
        """
        async with self._unit_of_work:
            user = await self._user_repository.get_by_id_with_relations(user_id)
            if not user or not user.security:
                raise ValueError("User not found")

            if not user.security.two_factor_enabled:
                raise ValueError("2FA must be enabled to regenerate backup codes")

            # Verify TOTP code
            if user.security.two_factor_secret:
                totp = pyotp.TOTP(user.security.two_factor_secret)
                if not totp.verify(verify_code, valid_window=1):
                    raise ValueError("Invalid TOTP code")

            # Generate new backup codes
            backup_codes = [secrets.token_hex(4) for _ in range(10)]
            user.security.two_factor_backup_codes = ",".join(backup_codes)
            await self._user_repository.save_security(user.security)
            await self._unit_of_work.commit()

            return {"backup_codes": backup_codes}
