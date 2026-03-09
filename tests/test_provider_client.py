from unittest.mock import AsyncMock, patch

import pytest

from src.service import event_provider_client
from tests.conftest import _make_response


def test_raise_for_status_raises_auth_error_on_401(client):
    """HTTP 401 превращается в EventsProviderAuthError."""
    resp = _make_response(401)
    with pytest.raises(event_provider_client.EventsProviderAuthError):
        client._raise_for_status(resp)


def test_raise_for_status_raises_not_found_on_404(client):
    """HTTP 404 превращается в EventsProviderNotFoundError."""
    resp = _make_response(404)
    with pytest.raises(event_provider_client.EventsProviderNotFoundError):
        client._raise_for_status(resp)


def test_raise_for_status_calls_raise_for_status_on_200(client):
    """HTTP 200, проверяем что вызвана проверка исключений была только один раз"""
    resp = _make_response(200, json_data={"ok": True})
    client._raise_for_status(resp)
    resp.raise_for_status.assert_called_once()


def test_raise_for_status_raises_seat_unavailable_on_400_already_sold(client):
    """HTTP 400 с сообщением 'already sold' превращается в EventsProviderSeatUnavailableError."""
    resp = _make_response(400, json_data="Этот билет не доступен (место уже занято).")
    with pytest.raises(event_provider_client.EventsProviderError):
        client._raise_for_status(resp)


def test_raise_for_status_raises_generic_error_on_400(client):
    """HTTP 400 без 'already sold' превращается в общий EventsProviderError."""
    resp = _make_response(400, json_data={"detail": "не корректные данные"})
    with pytest.raises(event_provider_client.EventsProviderError):
        client._raise_for_status(resp)


def test_raise_for_status_raises_error_on_503(client):
    """HTTP 503 также превращается в EventsProviderError."""
    resp = _make_response(503, text="Сервис не доступен")
    with pytest.raises(event_provider_client.EventsProviderError):
        client._raise_for_status(resp)


def test_first_events_url_builds_correct_url(client):
    """Проверяем правильно ли формируется url для первого запроса к API provider"""
    url = client.first_events_url("2000-01-01")
    assert url == "http://test-provider/api/events/?changed_at=2000-01-01"


def test_first_events_url_strips_trailing_slash_from_base_url():
    """
    Проверяем корректно ли обрабатывается лишний слеш(trailing slash)
    граничный случай, чтобы не получилось:
    так         http://test-provider/api/events/
    а не так    http://test-provider//api/events/
    """
    c = event_provider_client.EventsProviderClient(
        base_url="http://test-provider/", api_key="test-key"
    )
    url = c.first_events_url("2000-01-01")
    assert url == "http://test-provider/api/events/?changed_at=2000-01-01"


@pytest.mark.asyncio
async def test_events_page_returns_page_data(client):
    """
    Проверяем что при запросе получаем ожидаемые данные
    """
    page = {"next": None, "results": [{"id": "1"}]}
    mock_resp = _make_response(200, json_data=page)
    with patch("httpx.AsyncClient") as mock:
        # mock.return_value - httpx.AsyncClient
        # __aenter__.return_value - async with as client
        # .get = AsyncMock(return_value=mock_resp) - await client.get(url)
        mock.return_value.__aenter__.return_value.get = AsyncMock(
            return_value=mock_resp
        )
        result = await client.events_page(
            "http://test-provider/api/events/?changed_at=2000-01-01"
        )
    assert result == page
