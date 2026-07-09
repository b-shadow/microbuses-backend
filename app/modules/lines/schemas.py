from pydantic import BaseModel, ConfigDict


class LineCreateRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    nombre_linea: str | None = None
    color_linea: str | None = None


class LinePatchRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    nombre_linea: str | None = None
    color_linea: str | None = None
    is_active: bool | None = None
