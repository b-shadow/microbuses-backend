from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, UUIDPrimaryKeyMixin


class BusDriverAssignment(UUIDPrimaryKeyMixin, Base):
    __tablename__ = 'bus_driver_assignments'

    bus_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey('buses.id'), nullable=False, index=True)
    driver_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey('drivers.id'), nullable=False, index=True)
    assigned_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), nullable=False)
    removed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=False), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
