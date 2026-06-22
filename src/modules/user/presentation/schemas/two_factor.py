"""Request schemas for two-factor authentication endpoints."""

from pydantic import BaseModel, Field
from typing import Literal


class SetupTOTPRequest(BaseModel):
    """Request to set up TOTP 2FA."""
    pass


class VerifyTOTPSetupRequest(BaseModel):
    """Request to verify and enable TOTP 2FA."""
    code: str = Field(..., description="6-digit TOTP code from authenticator app")


class DisableTOTPRequest(BaseModel):
    """Request to disable TOTP 2FA."""
    code: str = Field(..., description="Current TOTP code or backup code")


class SendEmail2FACodeRequest(BaseModel):
    """Request to send a 2FA code via email."""
    pass


class VerifyEmail2FACodeRequest(BaseModel):
    """Request to verify an email-based 2FA code."""
    code: str = Field(..., description="6-digit verification code from email")


class RegenerateBackupCodesRequest(BaseModel):
    """Request to regenerate backup codes."""
    verify_code: str = Field(..., description="Current TOTP code for verification")


class Verify2FARequest(BaseModel):
    """Request to verify a 2FA code during login."""
    code: str = Field(..., description="2FA verification code")
    method: Literal["totp", "email", "backup"] = Field(
        default="totp",
        description="Verification method",
    )


class TwoFactorSetupResponse(BaseModel):
    """Response containing TOTP setup information."""
    secret: str
    uri: str
    qr_code_data: str


class TwoFactorEnableResponse(BaseModel):
    """Response containing backup codes after enabling 2FA."""
    backup_codes: list[str]


class TwoFactorVerifyResponse(BaseModel):
    """Response for 2FA verification."""
    success: bool
    message: str | None = None


class LoginWith2FAResponse(BaseModel):
    """Response when 2FA is required during login."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    two_factor_required: bool = True
