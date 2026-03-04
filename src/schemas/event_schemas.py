from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str


class PlaceBase(BaseModel):
    id: UUID
    name: str
    city: str
    address: str


class PlaceDetail(PlaceBase):
    seats_pattern: str


class EventListItem(BaseModel):
    id: UUID
    name: str
    place: PlaceBase
    event_time: datetime
    registration_deadline: datetime
    status: str
    number_of_visitors: int

    model_config = {"from_attributes": True}


class EventDetail(BaseModel):
    id: UUID
    name: str
    place: PlaceDetail
    event_time: datetime
    registration_deadline: datetime
    status: str
    number_of_visitors: int

    model_config = {"from_attributes": True}


class EventListResponse(BaseModel):
    count: int
    next: str | None
    previous: str | None
    results: list[EventListItem]
