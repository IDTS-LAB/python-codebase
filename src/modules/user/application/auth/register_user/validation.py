from src.modules.user.application.auth.register_user.command import RegisterUserCommand


def validate_register_user_command(command: RegisterUserCommand) -> None:
    if not command.password.strip():
        raise ValueError("Password is required")
    if len(command.password) < 8:
        raise ValueError("Password must contain at least 8 characters")
