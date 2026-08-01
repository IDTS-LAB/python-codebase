"""Commands for two-factor authentication operations."""

from pydantic import BaseModel
from typing import Literal


class SetupTOTPCommand(BaseModel):
    """Command to set up TOTP 2FA."""
    user_id: int


class VerifyTOTPSetupCommand(BaseModel):
    """Command to verify and enable TOTP 2FA."""
    user_id: int
    code: str


class DisableTOTPCommand(BaseModel):
    """Command to disable TOTP 2FA."""
    user_id: int
    code: str


class SendEmail2FACodeCommand(BaseModel):
    """Command to send a 2FA code via email."""
    user_id: int


class VerifyEmail2FACodeCommand(BaseModel):
    """Command to verify an email-based 2FA code."""
    user_id: int
    code: str


class RegenerateBackupCodesCommand(BaseModel):
    """Command to regenerate backup codes."""
    user_id: int
    verify_code: str


class Verify2FACommand(BaseModel):
    """Command to verify a 2FA code during login."""
    user_id: int
    code: str
    method: Literal["totp", "email", "backup"] = "totp"
