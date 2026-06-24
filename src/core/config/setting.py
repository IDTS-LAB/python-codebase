from functools import lru_cache
from typing import ClassVar, Optional

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DEFAULT_SECRET_KEY: ClassVar[str] = "super-secret-key-change-in-production"

    # Application metadata and runtime environment.
    APP_NAME: str = Field(alias="APP_NAME", default="Todo Modulith API")
    APP_ENV: str = Field(alias="APP_ENV", default="development")
    FRONTEND_URL: str = Field(alias="FRONTEND_URL", default="http://localhost:3000")

    # Database connection string and SQLAlchemy pool tuning.
    DATABASE_URL: str = Field(
        alias="DATABASE_URL",
        default="postgresql+asyncpg://postgres@localhost:5432/todo_db",
    )
    DATABASE_POOL_SIZE: int = Field(alias="DATABASE_POOL_SIZE", default=20)
    DATABASE_MAX_OVERFLOW: int = Field(alias="DATABASE_MAX_OVERFLOW", default=10)
    DATABASE_POOL_TIMEOUT: int = Field(alias="DATABASE_POOL_TIMEOUT", default=30)
    DATABASE_POOL_RECYCLE: int = Field(alias="DATABASE_POOL_RECYCLE", default=3600)

    # Redis connection used by shared infrastructure such as rate limiting or caching.
    REDIS_URL: str = Field(
        alias="REDIS_URL",
        default="redis://127.0.0.1:6379/0",
    )

    # JWT signing, validation, and token lifetime settings.
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

    # HTTP protection settings for rate limits, CORS, CSP, idempotency, and payload size.
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
    MAX_REQUEST_SIZE_MB: int = Field(
        alias="MAX_REQUEST_SIZE_MB", default=5 * 1024 * 1024
    )

    # Account lockout thresholds used to slow repeated failed login attempts.
    ACCOUNT_LOCKOUT_MAX_ATTEMPTS: int = Field(
        alias="ACCOUNT_LOCKOUT_MAX_ATTEMPTS", default=5
    )
    ACCOUNT_LOCKOUT_WINDOW_MINUTES: int = Field(
        alias="ACCOUNT_LOCKOUT_WINDOW_MINUTES", default=15
    )
    ACCOUNT_LOCKOUT_DURATION_MINUTES: int = Field(
        alias="ACCOUNT_LOCKOUT_DURATION_MINUTES", default=15
    )

    # Logging output format for application logs.
    LOG_FORMAT: str = Field(alias="LOG_FORMAT", default="json")

    # OpenTelemetry distributed tracing configuration.
    OTEL_ENABLED: bool = Field(alias="OTEL_ENABLED", default=False)
    OTEL_SERVICE_NAME: str = Field(
        alias="OTEL_SERVICE_NAME", default="fastapi-modulith"
    )
    OTEL_EXPORTER_OTLP_ENDPOINT: str = Field(
        alias="OTEL_EXPORTER_OTLP_ENDPOINT", default=""
    )
    OTEL_EXPORTER_OTLP_HEADERS: str = Field(
        alias="OTEL_EXPORTER_OTLP_HEADERS", default=""
    )

    # Email provider selection and provider-specific credentials.
    EMAIL_PROVIDER: str = Field(alias="EMAIL_PROVIDER", default="ses")

    # AWS SES configuration.
    AWS_REGION: str = Field(alias="AWS_REGION", default="us-east-1")
    AWS_ACCESS_KEY_ID: Optional[str] = Field(alias="AWS_ACCESS_KEY_ID", default=None)
    AWS_SECRET_ACCESS_KEY: Optional[str] = Field(
        alias="AWS_SECRET_ACCESS_KEY",
        default=None,
    )
    SES_FROM_EMAIL: str = Field(alias="SES_FROM_EMAIL", default="noreply@example.com")

    # SendGrid configuration.
    SENDGRID_API_KEY: Optional[str] = Field(alias="SENDGRID_API_KEY", default=None)
    SENDGRID_FROM_EMAIL: str = Field(
        alias="SENDGRID_FROM_EMAIL",
        default="noreply@example.com",
    )

    # SMTP configuration for Gmail or other SMTP providers.
    SMTP_HOST: Optional[str] = Field(alias="SMTP_HOST", default=None)
    SMTP_PORT: int = Field(alias="SMTP_PORT", default=587)
    SMTP_USERNAME: Optional[str] = Field(alias="SMTP_USERNAME", default=None)
    SMTP_PASSWORD: Optional[str] = Field(alias="SMTP_PASSWORD", default=None)
    SMTP_FROM_EMAIL: str = Field(alias="SMTP_FROM_EMAIL", default="noreply@example.com")
    SMTP_USE_TLS: bool = Field(alias="SMTP_USE_TLS", default=True)

    # Optional admin and development users created by database seeders.
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
