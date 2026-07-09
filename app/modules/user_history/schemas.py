from datetime import datetime

from pydantic import BaseModel, Field


class UserHistoryCreateRequest(BaseModel):
    estimated_time: int = Field(ge=0)
    walking_distance_m: float = Field(ge=0)
    transfers_count: int = Field(ge=0, le=3)
    origin_lat: float = Field(ge=-90, le=90)
    origin_lng: float = Field(ge=-180, le=180)
    destination_lat: float = Field(ge=-90, le=90)
    destination_lng: float = Field(ge=-180, le=180)
    route_summary_json: dict | None = None


class UserHistoryItemResponse(BaseModel):
    id: str
    estimated_time: int
    walking_distance_m: float
    transfers_count: int
    created_at: datetime
