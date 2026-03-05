from __future__ import annotations

import typing
from uuid import UUID


class IEventRepository(typing.Protocol):
    async def get(self, event_id: str | UUID): ...
    async def list_events(self, date_from, page: int, page_size: int): ...
    async def insert(self, event_data: dict) -> None: ...
    async def update(self, event_data: dict) -> None: ...


class IEventsProviderClient(typing.Protocol):
    # def register(
    #     self, event_id: str, first_name: str, last_name: str, email: str, seat: str
    # ) -> str: ...
    # def unregister(self, event_id: str, ticket_id: str) -> bool: ...
    async def seats(self, event_id: str) -> list[str]: ...


class EventNotFoundError(Exception):
    pass


class EventNotPublishedError(Exception):
    pass


class GetSeatsUsecase:
    def __init__(self, events: IEventRepository, client: IEventsProviderClient) -> None:
        self._events = events
        self._client = client

    async def do(self, event_id: str) -> list[str]:
        event = await self._events.get(event_id)
        if event is None:
            raise EventNotFoundError(f"Event {event_id} not found")
        if event.status != "published":
            raise EventNotPublishedError(f"Event {event_id} is not published")
        return await self._client.seats(event_id)
