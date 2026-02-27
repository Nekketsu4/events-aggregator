from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # Database
    database_url: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/events_aggregator"
    )

    # # Redis / Celery
    # redis_url: str = "redis://localhost:6379/0"

    # Events Provider API
    events_provider_base_url: str = "http://events-provider.dev-2.python-labs.ru"
    events_provider_api_key: str

    # # Sync settings
    # sync_changed_at_default: str = "2000-01-01"
    #
    # # Seats cache TTL in seconds
    # seats_cache_ttl: int = 30


settings = Settings()
