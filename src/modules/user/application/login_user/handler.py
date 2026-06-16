from src.core.security.jwt import JWTService
from src.core.security.password import PasswordSerrvice
from src.modules.user.application.login_user.command import LoginUserCommand
from src.modules.user.domain.exceptions.user_exception import UserNotFoundError
from src.modules.user.domain.repositories.user_repository import UserRepository
from src.shared.exceptions.credential_exception import InvalidCredentialsError


class LoginUserCommandHandler:
    def __init__(self, user_repository: UserRepository):
        self._user_repository = user_repository

    async def execute(self, command: LoginUserCommand) -> dict[str, str]:
        user = await self._user_repository.get_by_email(command.username)
        if user is None:
            raise UserNotFoundError

        if not user or not PasswordSerrvice.verify_password(
            command.password, user.password
        ):
            raise InvalidCredentialsError("Incorrect email or password")

        access_token = JWTService.create_access_token(
            data={
                "fullname": user.fullname,
                "email": user.email,
                "sub": str(user.id),
            }
        )

        return {"access_token": access_token}
