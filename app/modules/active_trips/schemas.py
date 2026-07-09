from pydantic import BaseModel, Field


class StartTripRequest(BaseModel):
    bus_id: str
    line_id: int
    route_id: int | None = None


class FinishTripResponse(BaseModel):
    message: str


class ActiveTripResponse(BaseModel):
    id: str
    started_at: str
    bus_id: str
    line_id: int
    status: str


class ActiveTripHistoryItem(BaseModel):
    id: str
    driver_id: str
    bus_id: str
    line_id: int
    status: str
