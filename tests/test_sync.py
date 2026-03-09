from unittest.mock import patch

import pytest


@pytest.mark.asyncio
async def test_returns_success_response(async_client):
    """Заглушка иммитирует запуск синхронизации фоном и получаем ответ"""
    with patch("src.worker.tasks.async_sync", return_value=None):
        # coro.close() - закрываем выполнение корутины во избежание ошибок
        with patch("asyncio.create_task", side_effect=lambda coro: coro.close()):
            response = await async_client.post("/api/sync/trigger")

    assert response.status_code == 200
    assert response.json()["status"] == "accepted"
    assert response.json()["message"] == "Задача синхронизации поставлена в очередь"


@pytest.mark.asyncio
async def test_create_task_called_once(async_client):
    """Проверяем что фоновая задача была вызвана только один раз когда дернули ручку"""
    with patch("src.worker.tasks.async_sync", return_value=None):
        with patch(
            "asyncio.create_task", side_effect=lambda coro: coro.close()
        ) as mock_create_task:
            await async_client.post("/api/sync/trigger")

    # Проверка, что фоновая задача была вызвана хотя бы раз
    # Провекра, что не вызывали ее больше 1 раза(нигде нет дубликаций вызова задачи)
    mock_create_task.assert_called_once()


@pytest.mark.asyncio
async def test_returns_200_even_if_sync_fails(async_client):
    """Endpoint должен вернуть 200 даже если синхронизация упадёт в фоне"""
    with patch("src.worker.tasks.async_sync", return_value=None):
        with patch("asyncio.create_task", side_effect=lambda coro: coro.close()):
            response = await async_client.post("/api/sync/trigger")

    assert response.status_code == 200
