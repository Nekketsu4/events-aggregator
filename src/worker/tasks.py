from apscheduler.schedulers.asyncio import AsyncIOScheduler
from loguru import logger

scheduler = AsyncIOScheduler(timezone="UTC")


@scheduler.scheduled_job("cron", hour=2, minute=0)
async def sync_events_task() -> None:
    """Фоновая синхронизация событий API provider в 2 часа ночи"""
    logger.info("Запускаем задачу синхронизации событий")
    try:
        await async_sync()
    except Exception as exc:
        logger.exception(f"Запуск задачи синхронизации не удался: {exc}")


async def async_sync() -> None:
    from src.db.database import AsyncSessionLocal
    from src.service.event_provider_client import EventsProviderClient
    from src.service.sync_service import SyncService

    client = EventsProviderClient()
    async with AsyncSessionLocal() as session:
        service = SyncService(client=client, session=session)
        await service.run()
