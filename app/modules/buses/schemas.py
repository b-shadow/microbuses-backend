from pydantic import BaseModel, Field


class BusCreateRequest(BaseModel):
    plate: str = Field(min_length=3)
    model: str
    seats_count: int = Field(ge=1)
    internal_number: str
    current_line_id: int
    photo_url: str | None = None


class BusPatchRequest(BaseModel):
    model: str | None = None
    seats_count: int | None = Field(default=None, ge=1)
    internal_number: str | None = None
    status: str | None = None
    photo_url: str | None = None


class BusChangeLineRequest(BaseModel):
    line_id: int


class BusAssignDriverRequest(BaseModel):
    driver_id: str


class BusRemoveDriverRequest(BaseModel):
    driver_id: str
