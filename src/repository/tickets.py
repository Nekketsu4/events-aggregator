import uuid
from datetime import datetime, timezone

from pydantic import EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.events import Ticket
from src.service.use_cases import ITicketRepository


class TicketRepository(ITicketRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, ticket_id: str | uuid.UUID) -> Ticket | None:
        result = await self._session.execute(
            select(Ticket).where(Ticket.ticket_id == uuid.UUID(str(ticket_id)))
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        ticket_id: str,
        event_id: str,
        first_name: str,
        last_name: str,
        email: EmailStr,
        seat: str,
    ) -> Ticket:
        ticket = Ticket(
            ticket_id=uuid.UUID(ticket_id),
            event_id=uuid.UUID(event_id),
            first_name=first_name,
            last_name=last_name,
            email=email,
            seat=seat,
            created_at=datetime.now(tz=timezone.utc),
        )
        self._session.add(ticket)
        await self._session.flush()
        return ticket

    async def delete(self, ticket_id: str | uuid.UUID) -> None:
        ticket = await self.get(ticket_id)
        if ticket:
            await self._session.delete(ticket)
            await self._session.flush()
