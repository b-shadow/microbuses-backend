from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from geoalchemy2 import Geometry
from sqlalchemy import DateTime, ForeignKey, Index, Numeric, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, UUIDPrimaryKeyMixin


class TrackingLocation(UUIDPrimaryKeyMixin, Base):
    __tablename__ = 'tracking_locations'
    __table_args__ = (Index('ix_tracking_locations_trip_recorded', 'active_trip_id', 'recorded_at'),)

    active_trip_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey('active_trips.id'), nullable=False, index=True)
    location = mapped_column(Geometry('POINT', srid=4326), nullable=False)
    speed: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 2), nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), server_default=func.now(), nullable=False)
