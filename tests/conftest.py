"""
Тесты для классов EventsProviderClient и EventsPaginator.
Имитация взаимодействия с API provider через unittest.mock
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from src.api.v1.endpoints.events import router
from src.cache.seat_cache import SeatsCache
from src.db.database import get_async_db_session
from src.service.event_provider_client import (
    EventsProviderClient,
)


@pytest.fixture
def client():
    return EventsProviderClient(
        base_url="http://test-provider",
        api_key="test-key",
    )


def _make_response(status_code: int, json_data=None, text: str = "") -> MagicMock:
    """Вспомогательная функция для подделки HTTP ответов"""
    resp = MagicMock()
    resp.status_code = status_code
    resp.text = text
    if json_data is not None:
        resp.json.return_value = json_data
    resp.raise_for_status = MagicMock()
    return resp


@pytest.fixture
def app():
    app = FastAPI()
    app.include_router(router, prefix="/api")

    async def override_db():
        yield AsyncMock()

    app.dependency_overrides[get_async_db_session] = override_db
    return app


@pytest.fixture
async def async_client(app):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


@pytest.fixture
def cache() -> SeatsCache:
    """Возвращает экземпляр SeatsCache с TTL 30 секунд для тестов."""
    return SeatsCache(ttl=30)
