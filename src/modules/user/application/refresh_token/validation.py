from src.modules.user.application.refresh_token.command import RefreshTokenCommand


def validate_refresh_token_command(command: RefreshTokenCommand) -> None:
    if not command.token.strip():
        raise ValueError("Refresh token is required")
