from pydantic import BaseModel


class VariantCreateRequest(BaseModel):
    line_id: str
    name: str
    description: str | None = None


class VariantPatchRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    is_active: bool | None = None
