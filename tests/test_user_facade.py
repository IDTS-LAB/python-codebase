import asyncio

import pytest

from src.modules.user.domain.entities.user import User
from src.modules.user.domain.exceptions.user_exception import UserNotFoundError
from src.modules.user.facade import UserModuleFacade


class FakeUserRepository:
    def __init__(self, user: User | None) -> None:
        self._user = user

    async def get_by_id_with_relations(self, user_id: int) -> User | None:
        if self._user is None or self._user.id != user_id:
            return None
        return self._user


def test_facade_returns_profile_with_int_id():
    facade = UserModuleFacade(FakeUserRepository(
        User(id=7, email="a@example.com", password_hash="x", username="alice")
    ))
    profile = asyncio.run(facade.get_user_profile(7))
    assert profile is not None
    assert profile.id == 7
    assert profile.email == "a@example.com"
    assert profile.username == "alice"


def test_facade_raises_user_not_found_for_unknown_user():
    facade = UserModuleFacade(FakeUserRepository(None))
    with pytest.raises(UserNotFoundError):
        asyncio.run(facade.get_user_profile(99))
