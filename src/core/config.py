import os

from loguru import logger
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # Настройки приложения
    # DEBUG: bool
    PROJECT_NAME: str = "events-aggregator"
    VERSION: str = "0.1.0"

    # REDIS
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DECODE_RESPONSE: bool = True

    # Events Provider API
    EVENTS_PROVIDER_BASE_URL: str = "http://events-provider.dev-2.python-labs.ru"
    EVENTS_PROVIDER_API_KEY: str = ""

    # БД локально
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = "5432"
    POSTGRES_USER: str = ""
    POSTGRES_DB: str = ""
    POSTGRES_PASSWORD: str = ""

    # БД в LMS
    POSTGRES_USERNAME: str = ""
    POSTGRES_DATABASE_NAME: str = ""
    POSTGRES_CONNECTION_STRING: str = ""

    # Database_url
    DATABASE_URL: str = ""

    # Логирование
    # FORMAT_LOG: str = "{time:YYYY-MM-DD at HH:mm:ss} | {level} | {message}"
    # LOG_ROTATION: str = "10 MB"

    @model_validator(mode="after")
    def build_database_url(self):
        if self.DATABASE_URL:
            self.DATABASE_URL = self._fix_scheme(self.DATABASE_URL)
            return self

        if self.POSTGRES_CONNECTION_STRING:
            self.DATABASE_URL = self._fix_scheme(self.POSTGRES_CONNECTION_STRING)
            return self

        user = self.POSTGRES_USERNAME or self.POSTGRES_USER
        password = self.POSTGRES_PASSWORD
        host = self.POSTGRES_HOST
        port = self.POSTGRES_PORT
        db = self.POSTGRES_DATABASE_NAME or self.POSTGRES_DB

        if host and user and db:
            self.DATABASE_URL = (
                f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{db}"
            )
            return self

        self.DATABASE_URL = "postgresql+asyncpg://admin:admin@db:5432/aggregator_db"
        return self

    @staticmethod
    def _fix_scheme(url: str) -> str:
        for prefix in ("postgres://", "postgresql://"):
            if url.startswith(prefix):
                return "postgresql+asyncpg://" + url[len(prefix)]
        return url

    @property
    def get_db(self) -> str:
        return self.DATABASE_URL


settings = Settings()


# # Настройка логирования
# log_file_path = os.path.join(
#     os.path.dirname(os.path.abspath(__file__)), "..", "logs", "log.txt"
# )
# logger.add(
#     log_file_path,
#     format=settings.FORMAT_LOG,
#     level="INFO",
#     rotation=settings.LOG_ROTATION,
# )
