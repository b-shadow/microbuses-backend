from typing import Literal

from pydantic import BaseModel, Field


class LatLng(BaseModel):
    lat: float
    lng: float


class RoutingRequest(BaseModel):
    origin: LatLng
    destination: LatLng
    max_transfers: int = Field(default=3, ge=0, le=3)
    boarding_mode: Literal['ANYWHERE_ON_ROUTE', 'STOPS_ONLY'] = Field(default='ANYWHERE_ON_ROUTE')

