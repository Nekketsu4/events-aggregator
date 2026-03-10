from apscheduler.schedulers.asyncio import AsyncIOScheduler
from loguru import logger

from src.service.sync_launch import launch_sync

scheduler = AsyncIOScheduler(timezone="UTC")


@scheduler.scheduled_job("cron", hour=2, minute=0)
async def sync_events_task() -> None:
    """Фоновая синхронизация событий API provider в 2 часа ночи"""
    logger.info("Запускаем задачу синхронизации событий")
    try:
        await launch_sync()
    except Exception as exc:
        logger.exception(f"Запуск задачи синхронизации не удался: {exc}")
