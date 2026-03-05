from __future__ import annotations

import typing
from datetime import datetime, timezone
from uuid import UUID

from loguru import logger
from pydantic import EmailStr


class IEventRepository(typing.Protocol):
    async def get(self, event_id: str | UUID): ...
    async def list_events(self, date_from, page: int, page_size: int): ...
    async def insert(self, event_data: dict) -> None: ...
    async def update(self, event_data: dict) -> None: ...


class ITicketRepository(typing.Protocol):
    async def get(self, ticket_id: str | UUID): ...
    async def create(
        self,
        ticket_id: str,
        event_id: str,
        first_name: str,
        last_name: str,
        email: EmailStr,
        seat: str,
    ): ...
    async def delete(self, ticket_id: str | UUID) -> None: ...


class IEventsProviderClient(typing.Protocol):
    async def register(
        self, event_id: str, first_name: str, last_name: str, email: EmailStr, seat: str
    ) -> str: ...
    async def unregister(self, event_id: str, ticket_id: str) -> bool: ...
    async def seats(self, event_id: str) -> list[str]: ...


class EventNotFoundError(Exception):
    pass


class EventNotPublishedError(Exception):
    pass


class RegistrationDeadlinePassedError(Exception):
    pass


class SeatUnavailableError(Exception):
    pass


class TicketNotFoundError(Exception):
    pass


class EventAlreadyPassedError(Exception):
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


class CreateTicketUsecase:
    def __init__(
        self,
        events: IEventRepository,
        tickets: ITicketRepository,
        client: IEventsProviderClient,
    ) -> None:
        self._events = events
        self._tickets = tickets
        self._client = client

    async def do(
        self,
        event_id: str,
        first_name: str,
        last_name: str,
        email: EmailStr,
        seat: str,
    ) -> str:
        event = await self._events.get(event_id)
        if event is None:
            raise EventNotFoundError(f"Event {event_id} not found")

        if event.status != "published":
            raise EventNotPublishedError(f"Event {event_id} is not published")

        now = datetime.now(tz=timezone.utc)
        if now > event.registration_deadline:
            raise RegistrationDeadlinePassedError("Registration deadline has passed")

        # Validate seat availability before hitting the provider
        available_seats = await self._client.seats(event_id)
        if seat not in available_seats:
            raise SeatUnavailableError(f"Seat {seat} is not available")

        ticket_id = await self._client.register(
            event_id=event_id,
            first_name=first_name,
            last_name=last_name,
            email=email,
            seat=seat,
        )

        await self._tickets.create(
            ticket_id=ticket_id,
            event_id=event_id,
            first_name=first_name,
            last_name=last_name,
            email=email,
            seat=seat,
        )

        logger.info("Ticket %s created for event %s seat %s", ticket_id, event_id, seat)
        return ticket_id


class CancelTicketUsecase:
    def __init__(
        self,
        events: IEventRepository,
        tickets: ITicketRepository,
        client: IEventsProviderClient,
    ) -> None:
        self._events = events
        self._tickets = tickets
        self._client = client

    async def do(self, ticket_id: str) -> bool:
        ticket = await self._tickets.get(ticket_id)
        if ticket is None:
            raise TicketNotFoundError(f"Ticket {ticket_id} not found")

        event = await self._events.get(str(ticket.event_id))
        if event is None:
            raise EventNotFoundError(f"Event {ticket.event_id} not found")

        now = datetime.now(tz=timezone.utc)
        if now > event.event_time:
            raise EventAlreadyPassedError("Cannot cancel registration for a past event")

        success = await self._client.unregister(
            event_id=str(ticket.event_id),
            ticket_id=ticket_id,
        )
        if success:
            await self._tickets.delete(ticket_id)

        logger.info("Ticket %s cancelled for event %s", ticket_id, ticket.event_id)
        return success
