import asyncio
from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.cache.seat_cache import seats_cache
from src.db.database import get_async_db_session
from src.repository.events import EventRepository
from src.repository.tickets import TicketRepository
from src.schemas import event_schemas, seat_schemas, sync_schemas, ticket_schemas
from src.service.event_provider_client import (
    EventsProviderClient,
    EventsProviderNotFoundError,
    EventsProviderSeatUnavailableError,
)
from src.service.use_cases import (
    CancelTicketUsecase,
    CreateTicketUsecase,
    EventAlreadyPassedError,
    EventNotFoundError,
    EventNotPublishedError,
    GetSeatsUsecase,
    IEventsProviderClient,
    RegistrationDeadlinePassedError,
    SeatUnavailableError,
    TicketNotFoundError,
)

router = APIRouter()

_provider_client: IEventsProviderClient = EventsProviderClient()


@router.post("/sync/trigger", response_model=sync_schemas.SyncTriggerResponse)
async def trigger_sync(session: AsyncSession = Depends(get_async_db_session)):
    """Запуск синхронизации событий API provider вручную"""
    from src.worker.tasks import _async_sync

    asyncio.create_task(_async_sync())
    return sync_schemas.SyncTriggerResponse(
        status="accepted", message="Задача синхронизации поставлена в очередь"
    )


@router.get("/events", response_model=event_schemas.EventListResponse)
async def list_events(
    request: Request,
    date_from: date | None = Query(
        None, description="Фильтрация событий даты (YYYY-MM-DD)"
    ),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_async_db_session),
):
    repo = EventRepository(session)
    total, events = await repo.list_events(
        date_from=date_from, page=page, page_size=page_size
    )

    base_url = str(request.base_url).rstrip("/")
    params = request.query_params._dict.copy()

    def build_url(p: int) -> str:
        params["page"] = str(p)
        qs = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{base_url}/api/events?{qs}"

    next_url = build_url(page + 1) if page * page_size < total else None
    prev_url = build_url(page - 1) if page > 1 else None

    results = [
        event_schemas.EventListItem(
            id=e.id,
            name=e.name,
            place=event_schemas.PlaceBase(
                id=e.place.id,
                name=e.place.name,
                city=e.place.city,
                address=e.place.address,
            ),
            event_time=e.event_time,
            registration_deadline=e.registration_deadline,
            status=e.status,
            number_of_visitors=e.number_of_visitors,
        )
        for e in events
    ]

    return event_schemas.EventListResponse(
        count=total, next=next_url, previous=prev_url, results=results
    )


@router.get("/events/{event_id}", response_model=event_schemas.EventDetail)
async def get_event(
    event_id: UUID, session: AsyncSession = Depends(get_async_db_session)
):
    repo = EventRepository(session)
    e = await repo.get(str(event_id))
    if e is None:
        raise HTTPException(status_code=404, detail="Event not found")

    return event_schemas.EventDetail(
        id=e.id,
        name=e.name,
        place=event_schemas.PlaceDetail(
            id=e.place.id,
            name=e.place.name,
            city=e.place.city,
            address=e.place.address,
            seats_pattern=e.place.seats_pattern,
        ),
        event_time=e.event_time,
        registration_deadline=e.registration_deadline,
        status=e.status,
        number_of_visitors=e.number_of_visitors,
    )


@router.get("/events/{event_id}/seats", response_model=seat_schemas.SeatsResponse)
async def get_seats(
    event_id: UUID, session: AsyncSession = Depends(get_async_db_session)
):
    event_id_str = str(event_id)

    cached = seats_cache.get(event_id_str)
    if cached is not None:
        return seat_schemas.SeatsResponse(event_id=event_id, available_seats=cached)

    repo = EventRepository(session)
    usecase = GetSeatsUsecase(events=repo, client=_provider_client)

    try:
        available_seats = await usecase.do(event_id_str)
    except EventNotFoundError:
        raise HTTPException(status_code=404, detail="Событие не найдено")
    except EventNotPublishedError:
        raise HTTPException(status_code=400, detail="Событие не опубликовано")
    except EventsProviderNotFoundError:
        raise HTTPException(status_code=404, detail="Событие не найдено в API provider")

    seats_cache.set(event_id_str, available_seats)
    return seat_schemas.SeatsResponse(
        event_id=event_id, available_seats=available_seats
    )


@router.post(
    "/tickets", response_model=ticket_schemas.CreateTicketResponse, status_code=201
)
async def create_ticket(
    body: ticket_schemas.CreateTicketRequest,
    session: AsyncSession = Depends(get_async_db_session),
):
    event_repo = EventRepository(session)
    ticket_repo = TicketRepository(session)
    usecase = CreateTicketUsecase(
        events=event_repo, tickets=ticket_repo, client=_provider_client
    )
    try:
        ticket_id = await usecase.do(
            event_id=str(body.event_id),
            first_name=body.first_name,
            last_name=body.last_name,
            email=body.email,
            seat=body.seat,
        )
    except EventNotFoundError:
        raise HTTPException(status_code=404, detail="Event not found")
    except EventNotPublishedError:
        raise HTTPException(status_code=400, detail="Event is not published")
    except RegistrationDeadlinePassedError:
        raise HTTPException(status_code=400, detail="Registration deadline has passed")
    except SeatUnavailableError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except EventsProviderSeatUnavailableError:
        raise HTTPException(status_code=400, detail="Seat is already taken")

    await session.commit()
    return ticket_schemas.CreateTicketResponse(ticket_id=UUID(ticket_id))


@router.delete(
    "/tickets/{ticket_id}", response_model=ticket_schemas.CancelTicketResponse
)
async def cancel_ticket(
    ticket_id: UUID, db: AsyncSession = Depends(get_async_db_session)
):
    event_repo = EventRepository(db)
    ticket_repo = TicketRepository(db)
    usecase = CancelTicketUsecase(
        events=event_repo, tickets=ticket_repo, client=_provider_client
    )

    try:
        success = await usecase.do(str(ticket_id))
    except TicketNotFoundError:
        raise HTTPException(status_code=404, detail="Ticket not found")
    except EventNotFoundError:
        raise HTTPException(status_code=404, detail="Event not found")
    except EventAlreadyPassedError:
        raise HTTPException(
            status_code=400, detail="Cannot cancel registration for a past event"
        )

    await db.commit()
    return ticket_schemas.CancelTicketResponse(success=success)
