from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, UUIDPrimaryKeyMixin


class ActiveTrip(UUIDPrimaryKeyMixin, Base):
    __tablename__ = 'active_trips'

    driver_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey('drivers.id'), nullable=False, index=True)
    bus_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey('buses.id'), nullable=False, index=True)
    line_id: Mapped[int] = mapped_column(ForeignKey('lineas.id_linea'), nullable=False, index=True)
    route_id: Mapped[Optional[int]] = mapped_column(ForeignKey('linea_ruta.id_linea_ruta'), nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), nullable=False)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=False), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default='ACTIVE', nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), nullable=False)
