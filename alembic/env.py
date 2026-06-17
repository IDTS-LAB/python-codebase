# alembic/env.py
import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context
from src.core.authorization.infrastructure.models.casbin_rule_model import (
    CasbinRuleModel,  # noqa: F401
)
from src.core.authorization.infrastructure.models.permission_model import (
    PermissionModel,  # noqa: F401
)
from src.core.authorization.infrastructure.models.role_model import (
    RoleModel,  # noqa: F401
)
from src.core.authorization.infrastructure.models.role_permission_model import (
    RolePermissionModel,  # noqa: F401
)
from src.core.authorization.infrastructure.models.user_has_role_model import (
    UserHasRoleModel,  # noqa: F401
)
from src.core.config.setting import get_settings
from src.modules.todo.infrastructure.models.todo_model import TodoModel  # noqa: F401
from src.modules.user.infrastructure.models.refresh_token_model import (
    RefreshTokenModel,  # noqa: F401
)
from src.modules.user.infrastructure.models.user_model import UserModel  # noqa: F401
from src.shared.database.model import Base

settings = get_settings()

print(
    "🔍 ALEMBIC DEBUG: Tables found in metadata ->", list(Base.metadata.tables.keys())
)

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations in 'online' mode with async engine."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
