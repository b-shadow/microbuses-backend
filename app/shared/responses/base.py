from pydantic import BaseModel, Field


class SuccessResponse(BaseModel):
    success: bool = True
    message: str = 'Operación realizada correctamente'
    data: dict | list | None = Field(default_factory=dict)
    meta: dict = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    success: bool = False
    message: str
    error_code: str
    details: dict = Field(default_factory=dict)
