import os

from loguru import logger
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # Настройки приложения
    # DEBUG: bool
    PROJECT_NAME: str
    VERSION: str

    # REDIS
    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_DECODE_RESPONSE: bool

    # Events Provider API
    EVENTS_PROVIDER_BASE_URL: str
    EVENTS_PROVIDER_API_KEY: str

    # БД
    POSTGRES_HOST: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_PORT: int
    POSTGRES_CONNECTION_STRING: str

    # Логирование
    FORMAT_LOG: str
    LOG_ROTATION: str

    @property
    def get_db(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
            f"{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


settings = Settings()


# Настройка логирования
log_file_path = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "logs", "log.txt"
)
logger.add(
    log_file_path,
    format=settings.FORMAT_LOG,
    level="INFO",
    rotation=settings.LOG_ROTATION,
)
