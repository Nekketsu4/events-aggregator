import asyncio
from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.cache.seat_cache import seats_cache
from src.db.database import get_async_db_session
from src.exceptions import event_exc
from src.exceptions.provider_client_exc import (
    EventsProviderNotFoundError,
    EventsProviderSeatUnavailableError,
)
from src.repository.events import EventRepository, IEventRepository
from src.repository.tickets import ITicketRepository, TicketRepository
from src.schemas import event_schemas, seat_schemas, sync_schemas, ticket_schemas
from src.service.event_provider_client import (
    get_provider_client,
)
from src.service.sync_launch import launch_sync
from src.service.use_cases import (
    CancelTicketUsecase,
    CreateTicketUsecase,
    GetSeatsUsecase,
)
from src.utils.utils import build_pagination_urls

router = APIRouter()


@router.post("/sync/trigger", response_model=sync_schemas.SyncTriggerResponse)
async def trigger_sync():
    """Запуск синхронизации событий API provider вручную"""

    asyncio.create_task(launch_sync())
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
    """
    Получить список событий подгруженные в БД
    """
    repo: IEventRepository = EventRepository(session)
    total, events = await repo.list_events(
        date_from=date_from, page=page, page_size=page_size
    )

    next_url, prev_url = build_pagination_urls(request, page, page_size, total)

    results = [event_schemas.EventListItem.model_validate(e) for e in events]

    return event_schemas.EventListResponse(
        count=total, next=next_url, previous=prev_url, results=results
    )


@router.get("/events/{event_id}", response_model=event_schemas.EventListItem)
async def get_event(
    event_id: UUID, session: AsyncSession = Depends(get_async_db_session)
):
    """
    Получить событие по ID подгруженное в БД
    """
    repo: IEventRepository = EventRepository(session)
    event = await repo.get(str(event_id))
    if event is None:
        raise HTTPException(status_code=404, detail="Событие не найдено")
    return event_schemas.EventListItem.model_validate(event)


@router.get("/events/{event_id}/seats", response_model=seat_schemas.SeatsResponse)
async def get_seats(
    event_id: UUID,
    session: AsyncSession = Depends(get_async_db_session),
    client=Depends(get_provider_client),
):
    """
    Получить список свободных мест на мероприятие(по ID)
    """
    event_id_str = str(event_id)

    cached = seats_cache.get(event_id_str)
    if cached is not None:
        return seat_schemas.SeatsResponse(event_id=event_id, available_seats=cached)

    repo: IEventRepository = EventRepository(session)
    usecase = GetSeatsUsecase(events=repo, client=client)

    try:
        available_seats = await usecase.do(event_id_str)
    except event_exc.EventNotFoundError:
        raise HTTPException(status_code=404, detail="Событие не найдено")
    except event_exc.EventNotPublishedError:
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
    client=Depends(get_provider_client),
):
    """
    Регистрация места на событие
    """
    event_repo: IEventRepository = EventRepository(session)
    ticket_repo: ITicketRepository = TicketRepository(session)
    usecase = CreateTicketUsecase(events=event_repo, tickets=ticket_repo, client=client)
    try:
        ticket_id = await usecase.do(
            event_id=str(body.event_id),
            first_name=body.first_name,
            last_name=body.last_name,
            email=body.email,
            seat=body.seat,
        )
    except event_exc.EventNotFoundError:
        raise HTTPException(status_code=404, detail="Событие не найдено")
    except event_exc.EventNotPublishedError:
        raise HTTPException(status_code=400, detail="Событие не опубликовано")
    except event_exc.RegistrationDeadlinePassedError:
        raise HTTPException(status_code=400, detail="Время для регистрации уже прошло")
    except event_exc.SeatUnavailableError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except EventsProviderSeatUnavailableError:
        raise HTTPException(status_code=400, detail="Место уже занято")

    await session.commit()
    return ticket_schemas.CreateTicketResponse(ticket_id=UUID(ticket_id))


@router.delete(
    "/tickets/{ticket_id}", response_model=ticket_schemas.CancelTicketResponse
)
async def cancel_ticket(
    ticket_id: UUID,
    session: AsyncSession = Depends(get_async_db_session),
    client=Depends(get_provider_client),
):
    """
    Отмена регистрации на событие
    """
    event_repo: IEventRepository = EventRepository(session)
    ticket_repo: ITicketRepository = TicketRepository(session)
    usecase = CancelTicketUsecase(events=event_repo, tickets=ticket_repo, client=client)

    try:
        success = await usecase.do(str(ticket_id))
    except event_exc.TicketNotFoundError:
        raise HTTPException(status_code=404, detail="Билет не найден")
    except event_exc.EventNotFoundError:
        raise HTTPException(status_code=404, detail="Событие не найдено")
    except event_exc.EventAlreadyPassedError:
        raise HTTPException(
            status_code=400,
            detail="Нельзя отменить регистрация на событие, которое уже прошло",
        )

    await session.commit()
    return ticket_schemas.CancelTicketResponse(success=success)
