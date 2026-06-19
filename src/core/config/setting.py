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
    SECURITY_CONTENT_SECURITY_POLICY: str = Field(
        alias="SECURITY_CONTENT_SECURITY_POLICY",
        default="default-src 'self'; frame-ancestors 'none'",
    )
    IDEMPOTENCY_TTL_SECONDS: int = Field(alias="IDEMPOTENCY_TTL_SECONDS", default=86400)
    ACCOUNT_LOCKOUT_MAX_ATTEMPTS: int = Field(
        alias="ACCOUNT_LOCKOUT_MAX_ATTEMPTS", default=5
    )
    ACCOUNT_LOCKOUT_WINDOW_MINUTES: int = Field(
        alias="ACCOUNT_LOCKOUT_WINDOW_MINUTES", default=15
    )
    ACCOUNT_LOCKOUT_DURATION_MINUTES: int = Field(
        alias="ACCOUNT_LOCKOUT_DURATION_MINUTES", default=15
    )
    LOG_FORMAT: str = Field(alias="LOG_FORMAT", default="json")
    SEED_ADMIN_EMAIL: str = Field(alias="SEED_ADMIN_EMAIL", default="")
    SEED_ADMIN_PASSWORD: str = Field(alias="SEED_ADMIN_PASSWORD", default="")
    SEED_ADMIN_USERNAME: str = Field(alias="SEED_ADMIN_USERNAME", default="admin")
    SEED_ADMIN_FULLNAME: str = Field(
        alias="SEED_ADMIN_FULLNAME",
        default="System Administrator",
    )
    SEED_DEVELOPMENT_USERS_PASSWORD: str = Field(
        alias="SEED_DEVELOPMENT_USERS_PASSWORD",
        default="",
    )
    MAX_REQUEST_SIZE_MB: int = Field(
        alias="MAX_REQUEST_SIZE_MB", default=5 * 1024 * 1024
    )
    DATABASE_POOL_SIZE: int = Field(alias="DATABASE_POOL_SIZE", default=20)
    DATABASE_MAX_OVERFLOW: int = Field(alias="DATABASE_MAX_OVERFLOW", default=10)
    DATABASE_POOL_TIMEOUT: int = Field(alias="DATABASE_POOL_TIMEOUT", default=30)
    DATABASE_POOL_RECYCLE: int = Field(alias="DATABASE_POOL_RECYCLE", default=3600)

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
        if not self.is_production:
            return self

        if self.SECRET_KEY == self.DEFAULT_SECRET_KEY:
            raise ValueError("SECRET_KEY must be changed in production")
        if not self.DATABASE_URL.strip():
            raise ValueError("DATABASE_URL must be set in production")
        if not self.REDIS_URL.strip():
            raise ValueError("REDIS_URL must be set in production")
        if not self.JWT_ISSUER.strip():
            raise ValueError("JWT_ISSUER must be set in production")
        if not self.JWT_AUDIENCE.strip():
            raise ValueError("JWT_AUDIENCE must be set in production")
        if self.ACCESS_TOKEN_EXPIRE_MINUTES <= 0:
            raise ValueError("ACCESS_TOKEN_EXPIRE_MINUTES must be positive")
        if self.REFRESH_TOKEN_EXPIRE_MINUTES <= 0:
            raise ValueError("REFRESH_TOKEN_EXPIRE_MINUTES must be positive")
        if "*" in self.cors_allow_origins:
            raise ValueError("CORS_ALLOW_ORIGINS cannot be wildcard in production")
        return self

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
