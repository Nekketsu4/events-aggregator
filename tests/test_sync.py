from unittest.mock import patch

import pytest


@pytest.mark.asyncio
async def test_returns_accepted_status(async_client):
    with patch("src.worker.tasks._async_sync", return_value=None):
        with patch("asyncio.create_task", side_effect=lambda coro: coro.close()):
            response = await async_client.post("/api/sync/trigger")

    assert response.status_code == 200
    assert response.json()["status"] == "accepted"


@pytest.mark.asyncio
async def test_returns_message(async_client):
    with patch("src.worker.tasks._async_sync", return_value=None):
        with patch("asyncio.create_task", side_effect=lambda coro: coro.close()):
            response = await async_client.post("/api/sync/trigger")

    assert "message" in response.json()
    assert response.json()["message"] == "Задача синхронизации поставлена в очередь"


@pytest.mark.asyncio
async def test_create_task_called_once(async_client):
    with patch("src.worker.tasks._async_sync", return_value=None):
        with patch(
            "asyncio.create_task", side_effect=lambda coro: coro.close()
        ) as mock_create_task:
            await async_client.post("/api/sync/trigger")

    mock_create_task.assert_called_once()


@pytest.mark.asyncio
async def test_returns_200_even_if_sync_fails(async_client):
    """Endpoint должен вернуть 200 даже если синхронизация упадёт в фоне"""
    with patch("src.worker.tasks._async_sync", return_value=None):
        with patch("asyncio.create_task", side_effect=lambda coro: coro.close()):
            response = await async_client.post("/api/sync/trigger")

    assert response.status_code == 200
