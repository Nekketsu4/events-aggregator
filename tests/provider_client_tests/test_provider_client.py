from unittest.mock import AsyncMock, patch

import pytest

from src.service.event_provider_client import EventsProviderClient
from tests.conftest import _make_response


def test_raise_for_status_calls_raise_for_status_on_200(client):
    resp = _make_response(200, json_data={"ok": True})
    client._raise_for_status(resp)
    resp.raise_for_status.assert_called_once()


def test_first_events_url_builds_correct_url(client):
    url = client.first_events_url("2010-01-01")
    assert url == "http://test-provider/api/events/?changed_at=2010-01-01"


def test_first_events_url_strips_trailing_slash_from_base_url():
    c = EventsProviderClient(base_url="http://test-provider/", api_key="test-key")
    url = c.first_events_url("2010-01-01")
    assert url == "http://test-provider/api/events/?changed_at=2010-01-01"


@pytest.mark.asyncio
async def test_events_page_returns_page_data(client):
    page = {"next": None, "results": [{"id": "1"}]}
    mock_resp = _make_response(200, json_data=page)
    with patch("httpx.AsyncClient") as mock_cls:
        mock_cls.return_value.__aenter__.return_value.get = AsyncMock(
            return_value=mock_resp
        )
        result = await client.events_page(
            "http://test-provider/api/events/?changed_at=2000-01-01"
        )
    assert result == page
