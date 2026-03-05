from uuid import UUID

from pydantic import BaseModel


class SeatsResponse(BaseModel):
    event_id: UUID
    available_seats: list[str]
