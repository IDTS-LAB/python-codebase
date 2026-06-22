from src.modules.user.application.auth.login_user.command import LoginUserCommand


def validate_login_user_command(command: LoginUserCommand) -> None:
    if not command.username.strip():
        raise ValueError("Username is required")
    if not command.password.strip():
        raise ValueError("Password is required")
