"""
Вынесена в отдельный модуль чтобы избежать циклических зависимостей
между src.worker.tasks и src.api
"""

from src.db.database import AsyncSessionLocal
from src.service.event_provider_client import get_provider_client
from src.service.sync_service import SyncService


async def launch_sync() -> None:
    """
    Создаёт сессию БД и запускает полный цикл синхронизации событий.
    Используется как планировщиком, так и эндпоинтом ручного запуска.
    """
    client = get_provider_client()
    async with AsyncSessionLocal() as session:
        service = SyncService(client=client, session=session)
        await service.run()
