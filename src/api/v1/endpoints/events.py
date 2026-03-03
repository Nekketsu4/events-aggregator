from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import get_async_db_session
from src.repository.events import EventRepository
from src.schemas import schemas

router = APIRouter()


@router.get("/events", response_model=schemas.EventListResponse)
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
        schemas.EventListItem(
            id=e.id,
            name=e.name,
            place=e.place,
            event_time=e.event_time,
            registration_deadline=e.registration_deadline,
            status=e.status,
            number_of_visitors=e.number_of_visitors,
        )
        for e in events
    ]

    return schemas.EventListResponse(
        count=total, next=next_url, previous=prev_url, results=results
    )


@router.get("/events/{event_id}", response_model=schemas.EventDetail)
async def get_event(event_id: UUID, db: AsyncSession = Depends(get_async_db_session)):
    repo = EventRepository(db)
    event = await repo.get(str(event_id))
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")

    return schemas.EventDetail(
        id=event.id,
        name=event.name,
        place=schemas.PlaceDetail(
            id=event.place.id,
            name=event.place.name,
            city=event.place.city,
            address=event.place.address,
            seats_pattern=event.place.seats_pattern,
        ),
        event_time=event.event_time,
        registration_deadline=event.registration_deadline,
        status=event.status,
        number_of_visitors=event.number_of_visitors,
    )
