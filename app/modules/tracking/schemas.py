from datetime import datetime

from pydantic import BaseModel, Field


class TrackingPointRequest(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)
    speed: float | None = Field(default=None, ge=0)
    recorded_at: datetime | None = None


class TrackingLocationRequest(TrackingPointRequest):
    active_trip_id: str


class TrackingBatchRequest(BaseModel):
    active_trip_id: str
    points: list[TrackingPointRequest]
