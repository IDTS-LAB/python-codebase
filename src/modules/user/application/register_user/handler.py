from src.core.security.password import PasswordSerrvice
from src.modules.user.application.register_user.command import RegisterUserCommand
from src.modules.user.domain.entities.user import User
from src.modules.user.domain.exceptions.user_exception import UserAlreadyExistsError
from src.modules.user.domain.repositories.user_repository import UserRepository
from src.core.authorization.domain.service import AuthorizationService
from src.core.authorization.permissions import DEFAULT_USER_ROLE
from src.shared.unit_of_work import UnitOfWork


class RegisterUserCommandHandler:
    def __init__(
        self,
        user_repository: UserRepository,
        unit_of_work: UnitOfWork,
        authorization_service: AuthorizationService,
    ):
        self._user_repository = user_repository
        self._unit_of_work = unit_of_work
        self._authorization_service = authorization_service

    async def execute(self, command: RegisterUserCommand) -> User:
        existing = await self._user_repository.get_by_email(command.email)
        if existing:
            raise UserAlreadyExistsError("Email already registered")

        hashed_password = PasswordSerrvice.hash(command.password)
        user = User.create(
            command.email,
            password=hashed_password,
        )
        async with self._unit_of_work:
            saved_user = await self._user_repository.save(user=user)
            await self._authorization_service.assign_role(
                subject=str(saved_user.id),
                role=DEFAULT_USER_ROLE,
            )
            await self._unit_of_work.commit()
            return saved_user
