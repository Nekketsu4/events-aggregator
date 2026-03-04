from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.sync_metadata import SyncMetadata


class SyncMetadataRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_or_create(self) -> SyncMetadata:
        result = await self._session.execute(select(SyncMetadata).limit(1))
        meta = result.scalar_one_or_none()
        if meta is None:
            meta = SyncMetadata(sync_status="pending")
            self._session.add(meta)
            await self._session.flush()
        return meta

    async def update(
        self,
        sync_status: str,
        last_sync_time: datetime | None = None,
        last_changed_at: str | None = None,
        error_message: str | None = None,
    ) -> None:
        meta = await self.get_or_create()
        meta.sync_status = sync_status
        if last_sync_time is not None:
            meta.last_sync_time = last_sync_time
        if last_changed_at is not None:
            meta.last_changed_at = last_changed_at
        if error_message is not None:
            meta.error_message = error_message
        await self._session.flush()
