from src.core.security.password import PasswordSerrvice
from src.modules.user.application.create_user.command import CreateUserCommand
from src.modules.user.domain.repositories.user_repository import UserRepository
from src.modules.user.domain.entities.user import User
from src.modules.user.domain.exceptions.user_exception import UserAlreadyExistsError


class CreateUserHandler:
    def __init__(self, user_repository: UserRepository):
        self._user_repository = user_repository

    async def execute(self, command: CreateUserCommand) -> User:
        existing = await self._user_repository.get_by_email(command.email)
        if existing:
            raise UserAlreadyExistsError("Email already registered")

        hashed_password = PasswordSerrvice.hash(command.password)
        user = User.create(command.email, hashed_password=hashed_password)
        return self._user_repository.save(user=user)
