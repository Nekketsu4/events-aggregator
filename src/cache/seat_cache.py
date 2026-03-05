import time
from dataclasses import dataclass, field


@dataclass
class _CacheEntry:
    value: list[str]
    expires_at: float


class SeatsCache:
    """Simple in-memory cache with TTL for available seats."""

    def __init__(self, ttl: int = 30) -> None:
        self._ttl = ttl
        self._store: dict[str, _CacheEntry] = field(default_factory=dict)  # type: ignore[assignment]
        self._store = {}

    def get(self, event_id: str) -> list[str] | None:
        entry = self._store.get(event_id)
        if entry is None:
            return None
        if time.monotonic() > entry.expires_at:
            del self._store[event_id]
            return None
        return entry.value

    def set(self, event_id: str, seats: list[str]) -> None:
        self._store[event_id] = _CacheEntry(
            value=seats,
            expires_at=time.monotonic() + self._ttl,
        )

    def invalidate(self, event_id: str) -> None:
        self._store.pop(event_id, None)


seats_cache = SeatsCache(ttl=30)
