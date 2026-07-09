from datetime import date
from typing import Optional

from sqlalchemy import Boolean, Date, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Driver(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = 'drivers'

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    ci: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(180), nullable=False)
    birth_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    sex: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    phone: Mapped[str] = mapped_column(String(50), nullable=False)
    license_category: Mapped[str] = mapped_column(String(20), nullable=False)
    photo_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    approval_status: Mapped[str] = mapped_column(String(20), default='PENDING', nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
