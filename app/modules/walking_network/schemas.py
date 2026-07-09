from pydantic import BaseModel, Field


class WalkingRouteRequest(BaseModel):
    origin_lat: float = Field(ge=-90, le=90)
    origin_lng: float = Field(ge=-180, le=180)
    destination_lat: float = Field(ge=-90, le=90)
    destination_lng: float = Field(ge=-180, le=180)


class WalkingRouteResponse(BaseModel):
    distance_m: float
    estimated_minutes: int
    geometry: list[dict]