"""
Клиент который взаимодействует с API event provider.
"""

from __future__ import annotations

from typing import Any, AsyncIterator

import httpx
from loguru import logger

from src.core.config import settings


class EventsProviderError(Exception):
    """Родительский класс для event provider ошибок"""


class EventsProviderAuthError(EventsProviderError):
    """
    Не авторизован 401, то есть отсутствует
     или предоставлен не верный API key
    """


class EventsProviderNotFoundError(EventsProviderError):
    """Не найден 404"""


class EventsProviderSeatUnavailableError(EventsProviderError):
    """Место уже занято 400"""


class EventsProviderClient:
    """HTTP клиент для взаимодействия с API event provider"""

    def __init__(
        self,
        base_url: str = settings.EVENTS_PROVIDER_BASE_URL,
        api_key: str = settings.EVENTS_PROVIDER_API_KEY,
        timeout: float = 30.0,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._headers = {"x-api-key": api_key}
        self._timeout = timeout

    async def _get(self, url: str) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.get(
                url, headers=self._headers, follow_redirects=True
            )
        self._raise_for_status(response)
        return response.json()

    @staticmethod
    def _raise_for_status(response: httpx.Response) -> None:
        if response.status_code == 401:
            raise EventsProviderAuthError("Отсутствует либо неверный API key")
        if response.status_code == 404:
            raise EventsProviderNotFoundError("Данные не найдены")
        if response.status_code == 400:
            try:
                detail = response.json()
            except Exception:
                detail = response.text
            if "already sold" in str(detail):
                raise EventsProviderSeatUnavailableError(str(detail))
            raise EventsProviderError(f"Bad request: {detail}")
        if response.status_code >= 500:
            raise EventsProviderError(
                f"Server error {response.status_code}: {response.text[:200]}"
            )
        response.raise_for_status()

    async def events_page(self, url: str) -> dict[str, Any]:
        return await self._get(url)

    def first_events_url(self, changed_at: str) -> str:
        url = f"{self._base_url}/api/events/?changed_at={changed_at}"
        return url

    async def seats(self, event_id: str) -> list[str]:
        url = f"{self._base_url}/api/events/{event_id}/seats/"
        data = await self._get(url)
        return data.get("seats", [])


class EventsPaginator:
    def __init__(self, client: EventsProviderClient, changed_at: str) -> None:
        self._client = client
        self._next_url: str | None = client.first_events_url(changed_at)
        self._buffer: list[dict[str, Any]] = []

    def __aiter__(self) -> AsyncIterator[dict[str, Any]]:
        return self

    async def __anext__(self) -> dict[str, Any]:
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
