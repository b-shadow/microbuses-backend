from pydantic import BaseModel, ConfigDict


class RoutePointCreateRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id_linea_ruta: int | None = None
    id_punto: int | None = None
    id_punto_dest: int | None = None
    orden: int | None = None
    distancia: float | None = None
    tiempo: float | None = None


class RoutePointPatchRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id_punto: int | None = None
    id_punto_dest: int | None = None
    orden: int | None = None
    distancia: float | None = None
    tiempo: float | None = None


class RoutePointReorderItem(BaseModel):
    id: str
    orden: int


class RoutePointReorderRequest(BaseModel):
    points: list[RoutePointReorderItem]
