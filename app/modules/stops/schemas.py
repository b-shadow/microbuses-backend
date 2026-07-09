from pydantic import BaseModel, ConfigDict


class StopCreateRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    latitud: float | None = None
    longitud: float | None = None
    descripcion: str | None = None
    stop: str | None = None


class StopPatchRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    latitud: float | None = None
    longitud: float | None = None
    descripcion: str | None = None
    stop: str | None = None
    is_active: bool | None = None
