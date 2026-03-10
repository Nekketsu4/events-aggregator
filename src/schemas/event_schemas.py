from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class _OrmBase(BaseModel):
    model_config = {"from_attributes": True}


class HealthResponse(BaseModel):
    status: str


class PlaceBase(_OrmBase):
    id: UUID
    name: str
    city: str
    address: str


class PlaceDetail(PlaceBase):
    seats_pattern: str


class PlaceDetailChangeCreate(PlaceDetail):
    changed_at: datetime
    created_at: datetime


class EventListItem(_OrmBase):
    id: UUID
    name: str
    place: PlaceDetail
    event_time: datetime
    registration_deadline: datetime
    status: str
    number_of_visitors: int


class EventDetail(BaseModel):
    id: UUID
    name: str
    place: PlaceDetailChangeCreate
    event_time: datetime
    registration_deadline: datetime
    status: str
    number_of_visitors: int
    changed_at: datetime
    created_at: datetime
    status_changed_at: datetime


class EventListResponse(BaseModel):
    count: int
    next: str | None
    previous: str | None
    results: list[EventListItem]
