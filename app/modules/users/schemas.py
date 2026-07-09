from pydantic import BaseModel, EmailStr


class UserUpdateRequest(BaseModel):
    names: str | None = None
    last_names: str | None = None
    phone: str | None = None
    photo_url: str | None = None


class UserChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str
    confirm_password: str


class UserProfileResponse(BaseModel):
    id: str
    email: EmailStr
    names: str | None
    last_names: str | None
    phone: str | None
    photo_url: str | None
    is_active: bool