from pydantic import BaseModel, ConfigDict


class RouteCreateRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id_linea: int | None = None
    id_ruta: int | None = None
    descripcion: str | None = None
    distancia: float | None = None
    tiempo: float | None = None


class RoutePatchRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    descripcion: str | None = None
    distancia: float | None = None
    tiempo: float | None = None
    is_active: bool | None = None
