"""
Тесты для SeatsCache — in-memory кэша мест с TTL.
Проверяют сохранение, получение, инвалидацию и истечение кэша.
"""

import time
from unittest.mock import patch


def test_get_returns_none_for_missing_key(cache):
    """get() возвращает None если ключ не был добавлен."""
    assert cache.get("nonexistent-event") is None


def test_set_and_get_returns_seats(cache):
    """set() сохраняет список мест, get() возвращает его."""
    seats = ["A1", "A2", "B1"]
    cache.set("event-1", seats)
    assert cache.get("event-1") == seats


def test_get_returns_none_after_ttl_expired(cache):
    """get() возвращает None если TTL кэша истёк."""
    cache.set("event-1", ["A1"])
    # Имитируем истечение TTL — сдвигаем время на 31 секунду вперёд
    with patch(
        "src.cache.seat_cache.time.monotonic", return_value=time.monotonic() + 31
    ):
        assert cache.get("event-1") is None


def test_expired_entry_is_removed_from_store(cache):
    """Просроченная запись удаляется из внутреннего хранилища при обращении."""
    cache.set("event-1", ["A1"])
    with patch(
        "src.cache.seat_cache.time.monotonic", return_value=time.monotonic() + 31
    ):
        cache.get("event-1")
    # После обращения к истёкшей записи она должна быть удалена
    assert "event-1" not in cache._store


def test_invalidate_removes_entry(cache):
    """invalidate() удаляет запись по ключу."""
    cache.set("event-1", ["A1"])
    cache.invalidate("event-1")
    assert cache.get("event-1") is None


def test_different_events_are_cached_independently(cache):
    """Кэш хранит данные разных событий независимо друг от друга."""
    cache.set("event-1", ["A1", "A2"])
    cache.set("event-2", ["B1", "B2"])

    assert cache.get("event-1") == ["A1", "A2"]
    assert cache.get("event-2") == ["B1", "B2"]


def test_get_returns_none_not_raises_for_missing(cache):
    """get() возвращает None (не исключение) для отсутствующего ключа."""
    result = cache.get("non-exist")
    assert result is None
