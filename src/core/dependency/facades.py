from fastapi import Depends

from src.core.database.postgres.session import get_unit_of_work
from src.modules.user.facade import UserModuleFacade
from src.shared.unit_of_work import UnitOfWork


def get_user_module_facade(
    uow: UnitOfWork = Depends(get_unit_of_work),
) -> UserModuleFacade:
    return UserModuleFacade(user_repository=uow.users)
