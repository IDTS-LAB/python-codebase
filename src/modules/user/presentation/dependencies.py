from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from core.database.session import get_db
from core.security.jwt import JWTService
from modules.user.application.create_user.handler import CreateUserHandler
from modules.user.application.repository.user_repository import UserRepository
from modules.user.intrastructure.repositories.user_repository import (
    SQLAlchemyUserRepository,
)


def get_user_repository(db: AsyncSession = Depends(get_db)) -> UserRepository:
    return SQLAlchemyUserRepository(db)


def get_register_handler(
    repo: UserRepository = Depends(get_user_repository),
) -> CreateUserHandler:
    return CreateUserHandler(repo)


async def get_current_user(
    token: str = Depends(lambda: None),
    user_repository: UserRepository = Depends(get_user_repository),
) -> dict:
    #  TODO: move to get by query
    payload = JWTService.decode_token(token)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Could not validate credentials")

    user = await user_repository.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
