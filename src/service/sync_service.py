from __future__ import annotations

import uuid
from datetime import datetime, timezone

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.exceptions.provider_client_exc import EventsProviderError
from src.repository.events import EventRepository
from src.repository.sync_metadata import SyncMetadataRepository
from src.schemas.event_schemas import EventDetail
from src.service.event_provider_client import (
    EventsPaginator,
    EventsProviderClient,
)


class SyncService:
    def __init__(
        self,
        client: EventsProviderClient,
        session: AsyncSession,
    ) -> None:
        self._client = client
        self._session = session
        self._event_repo = EventRepository(session)
        self._sync_repo = SyncMetadataRepository(session)

    async def run(self) -> None:
        """
        Запускаем синхронизацию событий
        Сперва получаем все данные с 2000-01-01,
        а после, получаем только измененные данные с последней синхронизации
        """
        meta = await self._sync_repo.get_or_create()
        changed_at = meta.last_changed_at or settings.SYNC_CHANGED_AT_DEFAULT

        logger.info(f"Запуск синхронизации с {changed_at}")
        await self._sync_repo.update(sync_status="running")
        await self._session.commit()

        max_changed_at: str | None = None
        synced_count = 0

        try:
            async for event_data in EventsPaginator(
                self._client, changed_at=changed_at
            ):
                event_id = str(uuid.UUID(event_data["id"]))
                parsed_data = EventDetail.model_validate(event_data)
                existing = await self._event_repo.get(event_id)
                if existing is None:
                    await self._event_repo.insert(parsed_data)
                else:
                    await self._event_repo.update(parsed_data)
                synced_count += 1

                event_changed = event_data.get("changed_at", "")
                if max_changed_at is None or event_changed > max_changed_at:
                    max_changed_at = event_changed

                # чтобы не было огромных транзакций, подсчитываем количество полученных элементов
                # если оно достигает 100, выполняем коммит
                if synced_count % 100 == 0:
                    await self._session.commit()
                    logger.info(f"Синхронизация {synced_count} событий")

            await self._session.commit()

            next_changed_at = changed_at
            if max_changed_at:
                next_changed_at = max_changed_at[:10]

            await self._sync_repo.update(
                sync_status="success",
                last_sync_time=datetime.now(tz=timezone.utc),
                last_changed_at=next_changed_at,
                error_message=None,
            )
            await self._session.commit()
            logger.info(
                f"Синхронизация выполнена успешно. Синхронизаций выполнено: {synced_count}"
            )

        except EventsProviderError as exc:
            await self._session.rollback()
            logger.exception(f"Ошибка синхронизации: {exc}")
            await self._sync_repo.update(
                sync_status="failed",
                error_message=str(exc),
            )
            await self._session.commit()
            raise
