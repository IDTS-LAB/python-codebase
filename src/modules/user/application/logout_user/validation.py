from uuid import UUID

from src.modules.user.application.logout_user.command import LogoutUserCommand


def validate_logout_user_command(command: LogoutUserCommand) -> None:
    try:
        UUID(command.user_id)
    except ValueError as exc:
        raise ValueError("User id must be a valid UUID") from exc

    if not command.access_token.strip():
        raise ValueError("Access token is required")
