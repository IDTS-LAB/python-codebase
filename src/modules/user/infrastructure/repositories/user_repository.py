from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.user.domain.entities.user import User
from src.modules.user.domain.repositories.user_repository import UserRepository
from src.modules.user.infrastructure.models.user_model import UserModel


class SQLAlchemyUserRepository(UserRepository):
    def __init__(self, db: AsyncSession):
        self._db = db

    async def get_by_email(self, email) -> User | None:
        result = await self._db.execute(
            select(UserModel).where(UserModel.email == email)
        )
        user_model = result.scalar_one_or_none()
        if user_model is None:
            return None

        return User(
            id=user_model.id,
            email=user_model.email,
            password=user_model.password,
            username=user_model.username,
            fullname=user_model.fullname,
            birthday=user_model.birthday,
        )

    async def get_by_id(self, user_id: UUID) -> User | None:
        result = await self._db.execute(select(UserModel).where(UserModel.id == user_id))
        user_model = result.scalar_one_or_none()
        if not user_model:
            return None
        return User(
            id=user_model.id,
            email=user_model.email,
            password=user_model.password,
            username=user_model.username,
            fullname=user_model.fullname,
            birthday=user_model.birthday,
        )

    async def save(self, user: User) -> User:
        user_model = UserModel(
            id=user.id,
            email=user.email,
            password=user.password,
            username=user.username,
            fullname=user.fullname,
            birthday=user.birthday,
        )
        self._db.add(user_model)
        await self._db.flush()
        await self._db.refresh(user_model)
        return User(
            id=user_model.id,
            email=user_model.email,
            password=user_model.password,
            username=user_model.username,
            fullname=user_model.fullname,
            birthday=user_model.birthday,
        )
