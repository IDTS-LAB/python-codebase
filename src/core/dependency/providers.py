from fastapi import Depends

from modules.user.providers import UserModuleProvider
from src.core.database.postgres.session import get_unit_of_work
from src.shared.unit_of_work import UnitOfWork


def get_user_module_provider(
    uow: UnitOfWork = Depends(get_unit_of_work),
) -> UserModuleProvider:
    return UserModuleProvider(user_repository=uow.users)
