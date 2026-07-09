from typing import Optional

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Bus(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = 'buses'

    plate: Mapped[str] = mapped_column(String(30), unique=True, index=True, nullable=False)
    model: Mapped[str] = mapped_column(String(120), nullable=False)
    seats_count: Mapped[int] = mapped_column(nullable=False)
    internal_number: Mapped[str] = mapped_column(String(50), nullable=False)
    current_line_id: Mapped[int] = mapped_column(ForeignKey('lineas.id_linea'), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(30), default='INACTIVE', nullable=False)
    photo_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
