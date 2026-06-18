from uuid import uuid4

import pytest

from src.modules.todo.application.create_todo.command import CreateTodoCommand
from src.modules.todo.application.create_todo.validation import (
    validate_create_todo_command,
)
from src.modules.todo.application.list_todo.query import GetTodosQuery
from src.modules.todo.application.list_todo.validation import validate_get_todos_query
from src.modules.todo.application.update_todo.command import UpdateTodoCommand
from src.modules.todo.application.update_todo.validation import (
    validate_update_todo_command,
)
from src.modules.user.application.detail_user.query import DetailUserQuery
from src.modules.user.application.detail_user.validation import (
    validate_detail_user_query,
)
from src.modules.user.application.login_user.command import LoginUserCommand
from src.modules.user.application.login_user.validation import (
    validate_login_user_command,
)
from src.modules.user.application.logout_user.command import LogoutUserCommand
from src.modules.user.application.logout_user.validation import (
    validate_logout_user_command,
)
from src.modules.user.application.refresh_token.command import RefreshTokenCommand
from src.modules.user.application.refresh_token.validation import (
    validate_refresh_token_command,
)
from src.modules.user.application.register_user.command import RegisterUserCommand
from src.modules.user.application.register_user.validation import (
    validate_register_user_command,
)


def test_create_todo_validation_rejects_blank_title():
    with pytest.raises(ValueError, match="Todo title is required"):
        validate_create_todo_command(CreateTodoCommand(title=" "))


def test_update_todo_validation_rejects_empty_command():
    with pytest.raises(ValueError, match="At least one todo field must be provided"):
        validate_update_todo_command(UpdateTodoCommand())


def test_login_validation_rejects_blank_credentials():
    with pytest.raises(ValueError, match="Username is required"):
        validate_login_user_command(LoginUserCommand(username=" ", password="secret"))

    with pytest.raises(ValueError, match="Password is required"):
        validate_login_user_command(LoginUserCommand(username="person", password=" "))


def test_refresh_validation_rejects_blank_token():
    with pytest.raises(ValueError, match="Refresh token is required"):
        validate_refresh_token_command(RefreshTokenCommand(token=" "))


def test_register_validation_rejects_short_password():
    with pytest.raises(ValueError, match="Password must contain at least 8 characters"):
        validate_register_user_command(
            RegisterUserCommand(email="person@example.com", password="short")
        )


def test_logout_validation_rejects_invalid_user_id():
    with pytest.raises(ValueError, match="User id must be a valid UUID"):
        validate_logout_user_command(
            LogoutUserCommand(user_id="not-a-uuid", access_token="access-token")
        )


def test_logout_validation_rejects_blank_access_token():
    with pytest.raises(ValueError, match="Access token is required"):
        validate_logout_user_command(
            LogoutUserCommand(user_id=str(uuid4()), access_token=" ")
        )


def test_query_validation_accepts_valid_queries():
    user_id = uuid4()

    validate_get_todos_query(GetTodosQuery(user_id=user_id))
    validate_detail_user_query(DetailUserQuery(user_id=user_id))
