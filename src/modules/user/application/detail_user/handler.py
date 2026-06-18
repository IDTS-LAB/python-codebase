from src.modules.user.application.detail_user.query import DetailUserQuery
from src.modules.user.application.detail_user.validation import validate_detail_user_query
from src.modules.user.domain.entities.user import User
from src.modules.user.domain.exceptions.user_exception import UserNotFoundError
from src.modules.user.domain.repositories.user_repository import UserRepository


class DetailUserQueryHandler:
    def __init__(self, user_repository: UserRepository):
        self._user_repository = user_repository

    async def execute(self, query: DetailUserQuery) -> User:
        validate_detail_user_query(query)

        user = await self._user_repository.get_by_id(query.user_id)
        if user is None:
            raise UserNotFoundError("User not found.")

        return User(
            id=user.id,
            username=user.username,
            fullname=user.fullname,
            email=user.email,
            password=user.password,
            birthday=user.birthday,
        )
