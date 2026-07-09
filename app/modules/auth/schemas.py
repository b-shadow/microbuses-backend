import re
from typing import Annotated

from pydantic import BaseModel, Field
from pydantic import functional_validators


def _parse_email(v: str) -> str:
    """Valida formato básico de email sin verificar si el dominio existe (acepta .local, etc.)."""
    if not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', v):
        raise ValueError('Email inválido')
    return v.lower().strip()


LenientEmail = Annotated[str, functional_validators.AfterValidator(_parse_email)]


class LoginRequest(BaseModel):
    email: LenientEmail
    password: str = Field(min_length=6, max_length=128)


class RegisterUserRequest(BaseModel):
    email: LenientEmail
    password: str = Field(min_length=6, max_length=128)
    names: str | None = None
    last_names: str | None = None
    phone: str | None = None


class RegisterDriverRequest(BaseModel):
    email: LenientEmail
    password: str = Field(min_length=6, max_length=128)
    ci: str
    full_name: str
    phone: str
    license_category: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = 'bearer'
    role: str
