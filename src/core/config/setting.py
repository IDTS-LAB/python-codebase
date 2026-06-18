from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = Field(alias="APP_NAME", default="Todo Modulith API")
    APP_ENV: str = Field(alias="APP_ENV", default="development")
    DATABASE_URL: str = Field(
        alias="DATABASE_URL",
        default="postgresql+asyncpg://user:password@localhost:5432/todo_db",
    )
    REDIS_URL: str = Field(
        alias="REDIS_URL",
        default="redis://:eYVX7EwVmmxKPCDmwMtyKVge8oLd2t81@127.0.0.1:6379/0",
    )
    SECRET_KEY: str = Field(
        alias="SECRET_KEY", default="super-secret-key-change-in-production"
    )
    ALGORITHM: str = Field(alias="ALGORITHM", default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        alias="ACCESS_TOKEN_EXPIRE_MINUTES", default=30
    )
    REFRESH_TOKEN_EXPIRE_MINUTES: int = Field(
        alias="REFRESH_TOKEN_EXPIRE_MINUTES", default=10080
    )
    RATE_LIMIT: str = Field(alias="RATE_LIMIT", default="100/minute")
    MAX_REQUEST_SIZE_MB: int = Field(
        alias="MAX_REQUEST_SIZE_MB", default=5 * 1024 * 1024
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
