from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Todo Modulith API"
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/todo_db"
    SECRET_KEY: str = "super-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 60 * 24 * 7

    class Config:
        env_file = ".env"


settings = Settings()
