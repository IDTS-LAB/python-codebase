from functools import lru_cache
from typing import ClassVar

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DEFAULT_SECRET_KEY: ClassVar[str] = "super-secret-key-change-in-production"

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
    SECRET_KEY: str = Field(alias="SECRET_KEY", default=DEFAULT_SECRET_KEY)
    ALGORITHM: str = Field(alias="ALGORITHM", default="HS256")
    JWT_ISSUER: str = Field(alias="JWT_ISSUER", default="todo-modulith-api")
    JWT_AUDIENCE: str = Field(alias="JWT_AUDIENCE", default="todo-modulith-client")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        alias="ACCESS_TOKEN_EXPIRE_MINUTES", default=30
    )
    REFRESH_TOKEN_EXPIRE_MINUTES: int = Field(
        alias="REFRESH_TOKEN_EXPIRE_MINUTES", default=10080
    )
    RATE_LIMIT: str = Field(alias="RATE_LIMIT", default="100/minute")
    CORS_ALLOW_ORIGINS: str = Field(
        alias="CORS_ALLOW_ORIGINS",
        default="http://localhost:3000",
    )
    CORS_ALLOW_METHODS: str = Field(alias="CORS_ALLOW_METHODS", default="*")
    CORS_ALLOW_HEADERS: str = Field(alias="CORS_ALLOW_HEADERS", default="*")
    MAX_REQUEST_SIZE_MB: int = Field(
        alias="MAX_REQUEST_SIZE_MB", default=5 * 1024 * 1024
    )

    @property
    def is_production(self) -> bool:
        return self.APP_ENV.lower() == "production"

    @property
    def cors_allow_origins(self) -> list[str]:
        return self._split_csv(self.CORS_ALLOW_ORIGINS)

    @property
    def cors_allow_methods(self) -> list[str]:
        return self._split_csv(self.CORS_ALLOW_METHODS)

    @property
    def cors_allow_headers(self) -> list[str]:
        return self._split_csv(self.CORS_ALLOW_HEADERS)

    @staticmethod
    def _split_csv(value: str) -> list[str]:
        return [item.strip() for item in value.split(",") if item.strip()]

    @model_validator(mode="after")
    def validate_production_security(self):
        if self.is_production and self.SECRET_KEY == self.DEFAULT_SECRET_KEY:
            raise ValueError("SECRET_KEY must be changed in production")
        return self

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
