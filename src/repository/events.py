import uuid
from datetime import date, datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.events import Event, Place


class EventRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, event_id: str | uuid.UUID) -> Event | None:
        result = await self._session.execute(
            select(Event)
            .options(selectinload(Event.place))
            .where(Event.id == uuid.UUID(str(event_id)))
        )
        return result.scalar_one_or_none()

    async def list_events(
        self,
        date_from: date | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[int, list[Event]]:
        query = select(Event).options(selectinload(Event.place))
        if date_from is not None:
            dt_from = datetime(
                date_from.year, date_from.month, date_from.day, tzinfo=timezone.utc
            )
            query = query.where(Event.event_time >= dt_from)

        count_query = select(func.count()).select_from(query.subquery())
        count_result = await self._session.execute(count_query)
        total = count_result.scalar_one()

        query = (
            query.order_by(Event.event_time)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await self._session.execute(query)
        events = list(result.scalars().all())
        return total, events

    async def insert(self, event_data: dict) -> None:
        place_data = event_data["place"]
        place_id = uuid.UUID(place_data["id"])

        place = await self._session.get(Place, place_id)
        if place is None:
            place = Place(
                id=place_id,
                name=place_data["name"],
                city=place_data["city"],
                address=place_data["address"],
                seats_pattern=place_data["seats_pattern"],
                changed_at=datetime.fromisoformat(place_data["changed_at"]),
                created_at=datetime.fromisoformat(place_data["created_at"]),
            )
        self._session.add(place)

        event_id = uuid.UUID(event_data["id"])
        event = Event(
            id=event_id,
            name=event_data["name"],
            place_id=place_id,
            event_time=datetime.fromisoformat(event_data["event_time"]),
            registration_deadline=datetime.fromisoformat(
                event_data["registration_deadline"]
            ),
            status=event_data["status"],
            number_of_visitors=event_data.get("number_of_visitors", 0),
            changed_at=datetime.fromisoformat(event_data["changed_at"]),
            created_at=datetime.fromisoformat(event_data["created_at"]),
            status_changed_at=datetime.fromisoformat(event_data["status_changed_at"]),
        )
        self._session.add(event)

        await self._session.flush()

    async def update(self, event_data: dict) -> None:
        place_data = event_data["place"]
        place_id = uuid.UUID(place_data["id"])

        place = await self._session.get(Place, place_id)
        if place is not None:
            place.name = place_data["name"]
            place.city = place_data["city"]
            place.address = place_data["address"]
            place.seats_pattern = place_data["seats_pattern"]
            place.changed_at = datetime.fromisoformat(place_data["changed_at"])
            place.created_at = datetime.fromisoformat(place_data["created_at"])

        event_id = uuid.UUID(event_data["id"])
        event = await self._session.get(Event, event_id)
        if event is not None:
            event.name = event_data["name"]
            event.place_id = place_id
            event.event_time = datetime.fromisoformat(event_data["event_time"])
            event.registration_deadline = datetime.fromisoformat(
                event_data["registration_deadline"]
            )
            event.status = event_data["status"]
            event.number_of_visitors = event_data.get("number_of_visitors", 0)
            event.changed_at = datetime.fromisoformat(event_data["changed_at"])
            event.created_at = datetime.fromisoformat(event_data["created_at"])
            event.status_changed_at = datetime.fromisoformat(
                event_data["status_changed_at"]
            )

        await self._session.flush()
