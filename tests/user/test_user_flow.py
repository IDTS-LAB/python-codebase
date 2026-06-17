import asyncio
from uuid import uuid4

from src.core import di
from src.core.security.password import PasswordSerrvice
from src.modules.user.application.register_user.command import RegisterUserCommand
from src.modules.user.application.register_user.handler import (
    RegisterUserCommandHandler,
)
from src.modules.user.domain.entities.user import User


class FakeUserRepository:
    def __init__(self):
        self.saved_user = None
        self.user = None

    async def get_by_email(self, email: str):
        return None

    async def get_by_id(self, user_id):
        return self.user if str(self.user.id) == str(user_id) else None

    async def save(self, user: User):
        self.saved_user = user
        return user


class FakeRequest:
    def __init__(self, user_id):
        self.state = type(
            "State",
            (),
            {"user_id": str(user_id), "token_payload": {"sub": str(user_id)}},
        )()


class FakeUnitOfWork:
    def __init__(self):
        self.committed = False
        self.rolled_back = False

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        if exc_type is not None or not self.committed:
            await self.rollback()
        return False

    async def commit(self):
        self.committed = True

    async def rollback(self):
        self.rolled_back = True


class FakeAuthorizationService:
    def __init__(self):
        self.assigned_roles = []

    async def can(self, subject: str, resource: str, action: str) -> bool:
        return True

    async def assign_role(self, subject: str, role: str) -> None:
        self.assigned_roles.append((subject, role))


def test_create_user_hashes_password_and_awaits_save():
    async def run():
        repo = FakeUserRepository()
        unit_of_work = FakeUnitOfWork()
        authorization_service = FakeAuthorizationService()
        handler = RegisterUserCommandHandler(repo, unit_of_work, authorization_service)

        user = await handler.execute(
            RegisterUserCommand(email="person@example.com", password="plain-secret")
        )

        assert isinstance(user, User)
        assert user.email == "person@example.com"
        assert user.password != "plain-secret"
        assert PasswordSerrvice.verify_password("plain-secret", user.password)
        assert repo.saved_user is user
        assert unit_of_work.committed is True
        assert unit_of_work.rolled_back is False
        assert authorization_service.assigned_roles == [(str(user.id), "user")]

    asyncio.run(run())


def test_get_current_user_reads_user_id_from_request_state(monkeypatch):
    async def run():
        repo = FakeUserRepository()
        repo.user = User(id=uuid4(), email="person@example.com", password="hashed")
        monkeypatch.setattr(di, "SQLAlchemyUserRepository", lambda db: repo)

        current_user = await di.get_current_user(request=FakeRequest(repo.user.id), db=None)

        assert current_user["id"] == repo.user.id
        assert current_user["email"] == repo.user.email
        assert current_user["raw_payload"] == {"sub": str(repo.user.id)}

    asyncio.run(run())
