from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class DriverCreateRequest(BaseModel):
    email: str
    password: str = Field(min_length=8)
    ci: str
    full_name: str
    birth_date: date | None = None
    sex: str | None = None
    phone: str
    license_category: str
    photo_url: str | None = None


class DriverUpdateRequest(BaseModel):
    full_name: str | None = None
    birth_date: date | None = None
    sex: str | None = None
    phone: str | None = None
    license_category: str | None = None
    photo_url: str | None = None
    is_active: bool | None = None


class DriverDecisionRequest(BaseModel):
    reason: str | None = None


class DriverStatusFilter(BaseModel):
    approval_status: Literal['PENDING', 'APPROVED', 'REJECTED'] | None = None
