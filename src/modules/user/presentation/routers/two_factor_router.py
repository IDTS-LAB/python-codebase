"""Router for two-factor authentication endpoints."""

from fastapi import APIRouter, Depends, HTTPException

from src.core.schemas.response import SuccessResponse
from src.modules.user.application.auth.two_factor.command import (
    DisableTOTPCommand,
    RegenerateBackupCodesCommand,
    SendEmail2FACodeCommand,
    SetupTOTPCommand,
    Verify2FACommand,
    VerifyEmail2FACodeCommand,
    VerifyTOTPSetupCommand,
)
from src.modules.user.presentation.dependency import (
    get_current_user_id,
    get_disable_totp_handler,
    get_regenerate_backup_codes_handler,
    get_send_email_2fa_code_handler,
    get_setup_totp_handler,
    get_verify_2fa_handler,
    get_verify_email_2fa_code_handler,
    get_verify_totp_setup_handler,
)
from src.modules.user.presentation.schemas.two_factor import (
    DisableTOTPRequest,
    RegenerateBackupCodesRequest,
    SendEmail2FACodeRequest,
    SetupTOTPRequest,
    TwoFactorEnableResponse,
    TwoFactorSetupResponse,
    TwoFactorVerifyResponse,
    Verify2FARequest,
    VerifyEmail2FACodeRequest,
    VerifyTOTPSetupRequest,
)

router = APIRouter(prefix="/2fa", tags=["Two-Factor Authentication"])


@router.post(
    "/setup/totp",
    response_model=SuccessResponse[TwoFactorSetupResponse],
    summary="Set up TOTP 2FA",
    description="Generate a TOTP secret and QR code URI for authenticator apps like Google Authenticator, Authy, etc.",
)
async def setup_totp(
    request: SetupTOTPRequest,
    current_user_id: str = Depends(get_current_user_id),
    handler: SetupTOTPHandler = Depends(get_setup_totp_handler),
):
    """Set up TOTP-based 2FA.

    This endpoint generates a TOTP secret and returns a URI that can be used
    to create a QR code for scanning with authenticator apps.

    Compatible with:
    - Google Authenticator
    - Authy
    - Microsoft Authenticator
    - Any TOTP-compatible authenticator app
    """
    command = SetupTOTPCommand(user_id=int(current_user_id))
    result = await handler.execute(command)

    return SuccessResponse(
        success=True,
        message="TOTP setup initiated. Scan the QR code with your authenticator app.",
        data=TwoFactorSetupResponse(**result),
    )


@router.post(
    "/verify/totp",
    response_model=SuccessResponse[TwoFactorEnableResponse],
    summary="Verify and enable TOTP 2FA",
    description="Verify the TOTP code from your authenticator app and enable 2FA.",
)
async def verify_totp_setup(
    request: VerifyTOTPSetupRequest,
    current_user_id: str = Depends(get_current_user_id),
    handler: VerifyTOTPSetupHandler = Depends(get_verify_totp_setup_handler),
):
    """Verify TOTP setup and enable 2FA.

    After scanning the QR code, submit the 6-digit code from your authenticator app
    to complete the setup. This will return backup codes - store them safely!
    """
    command = VerifyTOTPSetupCommand(
        user_id=int(current_user_id),
        code=request.code,
    )
    result = await handler.execute(command)

    return SuccessResponse(
        success=True,
        message="2FA enabled successfully. Store your backup codes safely!",
        data=TwoFactorEnableResponse(**result),
    )


@router.post(
    "/disable",
    response_model=SuccessResponse[TwoFactorVerifyResponse],
    summary="Disable 2FA",
    description="Disable two-factor authentication for your account.",
)
async def disable_totp(
    request: DisableTOTPRequest,
    current_user_id: str = Depends(get_current_user_id),
    handler: DisableTOTPHandler = Depends(get_disable_totp_handler),
):
    """Disable 2FA.

    Requires either a current TOTP code or a backup code to verify identity.
    """
    command = DisableTOTPCommand(
        user_id=int(current_user_id),
        code=request.code,
    )
    result = await handler.execute(command)

    if result:
        return SuccessResponse(
            success=True,
            message="2FA disabled successfully",
            data=TwoFactorVerifyResponse(success=True),
        )

    raise HTTPException(status_code=400, detail="Failed to disable 2FA")


@router.post(
    "/send-email-code",
    response_model=SuccessResponse[TwoFactorVerifyResponse],
    summary="Send 2FA code via email",
    description="Send a verification code to your registered email address.",
)
async def send_email_2fa_code(
    request: SendEmail2FACodeRequest,
    current_user_id: str = Depends(get_current_user_id),
    handler: SendEmail2FACodeHandler = Depends(get_send_email_2fa_code_handler),
):
    """Send a 2FA verification code via email.

    Alternative to TOTP for users who prefer email-based verification.
    The code will expire in 10 minutes.
    """
    command = SendEmail2FACodeCommand(user_id=int(current_user_id))
    result = await handler.execute(command)

    if result:
        return SuccessResponse(
            success=True,
            message="Verification code sent to your email",
            data=TwoFactorVerifyResponse(success=True),
        )

    raise HTTPException(status_code=500, detail="Failed to send email")


@router.post(
    "/verify-email-code",
    response_model=SuccessResponse[TwoFactorVerifyResponse],
    summary="Verify email 2FA code",
    description="Verify a 2FA code received via email.",
)
async def verify_email_2fa_code(
    request: VerifyEmail2FACodeRequest,
    current_user_id: str = Depends(get_current_user_id),
    handler: VerifyEmail2FACodeHandler = Depends(get_verify_email_2fa_code_handler),
):
    """Verify an email-based 2FA code."""
    command = VerifyEmail2FACodeCommand(
        user_id=int(current_user_id),
        code=request.code,
    )
    result = await handler.execute(command)

    if result:
        return SuccessResponse(
            success=True,
            message="Email verification successful",
            data=TwoFactorVerifyResponse(success=True),
        )

    raise HTTPException(status_code=400, detail="Invalid or expired code")


@router.post(
    "/regenerate-backup-codes",
    response_model=SuccessResponse[TwoFactorEnableResponse],
    summary="Regenerate backup codes",
    description="Generate new backup codes for account recovery.",
)
async def regenerate_backup_codes(
    request: RegenerateBackupCodesRequest,
    current_user_id: str = Depends(get_current_user_id),
    handler: RegenerateBackupCodesHandler = Depends(
        get_regenerate_backup_codes_handler
    ),
):
    """Regenerate backup codes.

    This will invalidate all previous backup codes and generate new ones.
    Requires a current TOTP code for verification.
    """
    command = RegenerateBackupCodesCommand(
        user_id=int(current_user_id),
        verify_code=request.verify_code,
    )
    result = await handler.execute(command)

    return SuccessResponse(
        success=True,
        message="New backup codes generated. Store them safely!",
        data=TwoFactorEnableResponse(**result),
    )


@router.post(
    "/verify",
    response_model=SuccessResponse[TwoFactorVerifyResponse],
    summary="Verify 2FA code",
    description="Verify a 2FA code (used during login flow).",
)
async def verify_2fa(
    request: Verify2FARequest,
    current_user_id: str = Depends(get_current_user_id),
    handler: Verify2FAHandler = Depends(get_verify_2fa_handler),
):
    """Verify a 2FA code.

    Used in the login flow when 2FA is required.
    Supports TOTP, email, and backup code methods.
    """
    command = Verify2FACommand(
        user_id=int(current_user_id),
        code=request.code,
        method=request.method,
    )
    result = await handler.execute(command)

    if result:
        return SuccessResponse(
            success=True,
            message="2FA verification successful",
            data=TwoFactorVerifyResponse(success=True),
        )

    raise HTTPException(status_code=400, detail="Invalid 2FA code")
