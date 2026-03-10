from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.utils.utils import fix_scheme


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # Настройки приложения
    PROJECT_NAME: str = "events-aggregator"
    VERSION: str = "0.1.0"

    # Events Provider API
    EVENTS_PROVIDER_BASE_URL: str = ""
    EVENTS_PROVIDER_API_KEY: str = ""

    # БД локально
    POSTGRES_HOST: str = ""
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = ""
    POSTGRES_DB: str = ""
    POSTGRES_PASSWORD: str = ""

    # БД в LMS
    POSTGRES_USERNAME: str = ""
    POSTGRES_DATABASE_NAME: str = ""
    POSTGRES_CONNECTION_STRING: str = ""

    # Database_url
    DATABASE_URL: str = ""

    # конфиги для синхронизации
    SYNC_CHANGED_AT_DEFAULT: str = "2000-01-01"

    # кэширование TTL в секундах
    SEATS_CACHE_TTL: int = 30

    @model_validator(mode="after")
    def build_database_url(self):
        if self.DATABASE_URL:
            self.DATABASE_URL = fix_scheme(self.DATABASE_URL)
            return self

        if self.POSTGRES_CONNECTION_STRING:
            self.DATABASE_URL = fix_scheme(self.POSTGRES_CONNECTION_STRING)
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

    @property
    def get_db(self) -> str:
        return self.DATABASE_URL


settings = Settings()
