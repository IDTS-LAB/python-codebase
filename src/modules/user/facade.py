from pydantic import BaseModel

from src.modules.user.application.detail_user.handler import DetailUserQueryHandler
from src.modules.user.application.detail_user.query import DetailUserQuery
from src.modules.user.domain.repositories.user_repository import UserRepository
from src.shared.facade import ModuleFacade


class UserProfile(BaseModel):
    id: int
    email: str
    username: str | None = None


class UserModuleFacade(ModuleFacade):
    def __init__(self, user_repository: UserRepository):
        self._user_detail_query = DetailUserQueryHandler(
            user_repository=user_repository
        )

    async def get_user_profile(self, user_id: int) -> UserProfile | None:
        user = await self._user_detail_query.execute(
            DetailUserQuery(user_id=user_id)
        )
        if user is None:
            return None

        return UserProfile(
            id=user.id,
            email=user.email,
            username=user.username,
        )
