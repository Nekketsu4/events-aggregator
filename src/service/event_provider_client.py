"""
Клиент который взаимодействует с API event provider.
"""

from __future__ import annotations

from typing import Any, AsyncIterator

import httpx
from loguru import logger
from pydantic import EmailStr

from src.core.config import settings
from src.exceptions.provider_client_exc import raise_for_status


class EventsProviderClient:
    """HTTP клиент для взаимодействия с API event provider"""

    def __init__(
        self,
        base_url: str = settings.EVENTS_PROVIDER_BASE_URL,
        api_key: str = settings.EVENTS_PROVIDER_API_KEY,
        timeout: float = 30.0,
    ) -> None:
        """
        Инициализирует клиент и создаёт переиспользуемый httpx.AsyncClient.
        base_url: Базовый URL Events Provider API.
        api_key: Ключ аутентификации для заголовка x-api-key.
        timeout: Таймаут HTTP-запросов в секундах.
        """
        self._base_url = base_url.rstrip("/")
        self._http = httpx.AsyncClient(
            headers={"x-api-key": api_key},
            timeout=timeout,
            follow_redirects=True,
        )

    async def _get(self, url: str) -> dict[str, Any]:
        response = await self._http.get(url)
        raise_for_status(response)
        return response.json()

    async def _post(self, url: str, json: dict[str, Any]) -> dict[str, Any]:
        response = await self._http.post(url, json=json)
        raise_for_status(response)
        return response.json()

    async def _delete(self, url: str, json: dict[str, Any]) -> dict[str, Any]:
        response = await self._http.request("DELETE", url, json=json)
        raise_for_status(response)
        return response.json()

    async def events_page(self, url: str) -> dict[str, Any]:
        """Получает одну страницу событий по заданному URL."""
        return await self._get(url)

    def first_events_url(self, changed_at: str) -> str:
        """Формирует URL первой страницы запроса событий с фильтром по дате изменения."""
        url = f"{self._base_url}/api/events/?changed_at={changed_at}"
        return url

    async def seats(self, event_id: str) -> list[str]:
        """Получает список свободных мест для указанного события."""
        url = f"{self._base_url}/api/events/{event_id}/seats/"
        data = await self._get(url)
        return data.get("seats", [])

    async def register(
        self,
        event_id: str,
        first_name: str,
        last_name: str,
        email: EmailStr,
        seat: str,
    ) -> str:
        """Регистрирует участника на событие."""
        url = f"{self._base_url}/api/events/{event_id}/register/"
        data = await self._post(
            url,
            json={
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "seat": seat,
            },
        )
        return data["ticket_id"]

    async def unregister(self, event_id: str, ticket_id: str) -> bool:
        """Отменяет регистрацию участника на мероприятие."""
        url = f"{self._base_url}/api/events/{event_id}/unregister/"
        data = await self._delete(url, json={"ticket_id": ticket_id})
        return data.get("success", False)

    async def close(self) -> None:
        """Закрывает HTTP-соединение. Вызывать при завершении приложения."""
        await self._http.aclose()


class EventsPaginator:
    """Асинхронный итератор для обхода всех страниц событий."""

    def __init__(self, client: EventsProviderClient, changed_at: str) -> None:
        self._client = client
        self._next_url: str | None = client.first_events_url(changed_at)
        self._buffer: list[dict[str, Any]] = []

    def __aiter__(self) -> AsyncIterator[dict[str, Any]]:
        return self

    async def __anext__(self) -> dict[str, Any]:
        """
        Возвращает следующее событие, подгружая страницы по мере необходимости.
        Returns: Словарь с данными одного события.
        Raises: StopAsyncIteration: Когда все страницы пройдены.
        """
        while not self._buffer:
            if self._next_url is None:
                raise StopAsyncIteration
            logger.debug(
                f"Получаем страницу: {self._next_url}",
            )
            page = await self._client.events_page(self._next_url)
            self._next_url = page.get("next")
            results = page.get("results", [])
            if not results:
                raise StopAsyncIteration
            self._buffer.extend(results)

        return self._buffer.pop(0)


provider_client = EventsProviderClient()


def get_provider_client() -> EventsProviderClient:
    """Возвращает единственный экземпляр клиента. Используется как FastAPI зависимость."""
    return provider_client
