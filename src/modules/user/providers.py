from datetime import date

from pydantic import BaseModel

from src.modules.user.application.detail_user.handler import DetailUserQueryHandler
from src.modules.user.application.detail_user.query import DetailUserQuery
from src.modules.user.domain.repositories.user_repository import UserRepository


class UserProfile(BaseModel):
    id: str
    email: str
    username: str | None = None
    fullname: str | None = None
    birthday: date | None = None


class UserModuleProvider:
    def __init__(self, user_repository: UserRepository):
        self._user_detail_query = DetailUserQueryHandler(
            user_repository=user_repository
        )

    async def get_user_profile(self, user_id: str) -> UserProfile | None:
        user = await self._user_detail_query.execute(
            DetailUserQuery(user_id=str(user_id))
        )
        if user is None:
            return None

        return UserProfile(
            id=str(user.id),
            email=user.email,
            username=user.username,
            fullname=user.fullname,
            birthday=user.birthday,
        )
