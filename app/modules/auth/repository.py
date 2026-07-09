from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.admins.models import Admin
from app.modules.drivers.models import Driver
from app.modules.users.models import User


class AuthRepository:
    def find_by_email(self, db: Session, email: str) -> tuple[str, Any] | None:
        user = db.scalar(select(User).where(User.email == email))
        if user:
            return ('USER', user)
        driver = db.scalar(select(Driver).where(Driver.email == email))
        if driver:
            return ('DRIVER', driver)
        admin = db.scalar(select(Admin).where(Admin.email == email))
        if admin:
            return (admin.role, admin)
        return None
