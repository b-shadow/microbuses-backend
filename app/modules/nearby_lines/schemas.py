from pydantic import BaseModel, Field


class NearbyLinesSearchRequest(BaseModel):
    lat: float
    lng: float
    radius_m: float = Field(default=300, ge=10, le=2000)
