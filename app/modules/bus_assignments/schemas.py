from pydantic import BaseModel


class BusAssignmentCreateRequest(BaseModel):
    bus_id: str
    driver_id: str


class BusAssignmentRemoveRequest(BaseModel):
    bus_id: str
    driver_id: str
