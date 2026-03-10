import time
from dataclasses import dataclass

from src.core.config import settings


@dataclass
class _CacheEntry:
    value: list[str]
    expires_at: float


class SeatsCache:
    """
    Кэширование мест с помощью in-memory
    и установка времени жизни кэша
    """

    def __init__(self, ttl: int = 30) -> None:
        self._ttl = ttl
        self._store = {}

    def get(self, event_id: str) -> list[str] | None:
        """Возвращает список мест из кэша или None если запись истекла или отсутствует"""
        entry = self._store.get(event_id)
        if entry is None:
            return None
        if time.monotonic() > entry.expires_at:
            del self._store[event_id]
            return None
        return entry.value

    def set(self, event_id: str, seats: list[str]) -> None:
        """Сохраняет список мест в кэш"""
        self._store[event_id] = _CacheEntry(
            value=seats,
            expires_at=time.monotonic() + self._ttl,
        )

    def invalidate(self, event_id: str) -> None:
        """Удаляет запись из кэша"""
        self._store.pop(event_id, None)


seats_cache = SeatsCache(ttl=settings.SEATS_CACHE_TTL)
