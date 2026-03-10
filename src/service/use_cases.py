from __future__ import annotations

import typing
import uuid
from datetime import datetime, timezone

from loguru import logger
from pydantic import EmailStr

from src.exceptions.event_exc import (
    EventAlreadyPassedError,
    EventNotFoundError,
    EventNotPublishedError,
    RegistrationDeadlinePassedError,
    SeatUnavailableError,
    TicketNotFoundError,
)
from src.models.events import Event
from src.schemas.event_schemas import EventDetail


class IEventsProviderClient(typing.Protocol):
    async def register(
        self, event_id: str, first_name: str, last_name: str, email: EmailStr, seat: str
    ) -> str: ...
    async def unregister(self, event_id: str, ticket_id: str) -> bool: ...
    async def seats(self, event_id: str) -> list[str]: ...


class IEventRepository(typing.Protocol):
    async def get(self, event_id: str | uuid.UUID): ...
    async def list_events(
        self, date_from, page: int, page_size: int
    ) -> tuple[int, list[Event]]: ...
    async def insert(self, event_data: EventDetail) -> None: ...
    async def update(self, event_data: EventDetail) -> None: ...


class ITicketRepository(typing.Protocol):
    async def get(self, ticket_id: str | uuid.UUID): ...
    async def create(
        self,
        ticket_id: str,
        event_id: str,
        first_name: str,
        last_name: str,
        email: EmailStr,
        seat: str,
    ): ...
    async def delete(self, ticket_id: str | uuid.UUID) -> None: ...


class GetSeatsUsecase:
    """
    Возвращает список свободных мест.
    Проверяет существование события и его статус (должен быть "published"),
    затем запрашивает места у провайдера.
    """

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
    """
    Ищем событие, проверяем дедлайн события,
    проверяем доступно ли место,
    делаем регистрацию и сохраняем билет в БД.
    """

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
            raise EventNotFoundError(f"Событие {event_id} не найдено")

        if event.status != "published":
            raise EventNotPublishedError(f"Событие {event_id} не опубликовано")

        now = datetime.now(tz=timezone.utc)
        if now > event.registration_deadline:
            raise RegistrationDeadlinePassedError("Срок регистрации уже прошел")

        # Делаем проверку доступно ли место или нет
        available_seats = await self._client.seats(event_id)
        if seat not in available_seats:
            raise SeatUnavailableError(f"Место {seat} не доступно")

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

        logger.info(
            f"Билет> {ticket_id} создан для события {event_id}, ваше место {seat}"
        )
        return ticket_id


class CancelTicketUsecase:
    """
    Отмена билета. Ищем билет и событие в БД,
    проверяем что событие ещё не прошло,вызываем unregister у провайдера
    для удаления билета из БД.
    """

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
            raise TicketNotFoundError(f"Билет {ticket_id} не найден")

        event = await self._events.get(str(ticket.event_id))
        if event is None:
            raise EventNotFoundError(f"Событие {ticket.event_id} не найдено")

        now = datetime.now(tz=timezone.utc)
        if now > event.event_time:
            raise EventAlreadyPassedError(
                "Невозможно отменить событие на прошедшее событие"
            )

        success = await self._client.unregister(
            event_id=str(ticket.event_id),
            ticket_id=ticket_id,
        )
        if success:
            await self._tickets.delete(ticket_id)

        logger.info(f"Отменен билет {ticket_id} для события {ticket.event_id}")
        return success
