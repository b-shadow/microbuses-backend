from pydantic import BaseModel, Field


class AdminCreateRequest(BaseModel):
    email: str
    password: str = Field(min_length=8)
    full_name: str
    role: str = Field(default='ADMIN')


class AdminUpdateRequest(BaseModel):
    full_name: str | None = None
    role: str | None = None
    is_active: bool | None = None
