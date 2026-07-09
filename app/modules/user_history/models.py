from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from geoalchemy2 import Geometry
from sqlalchemy import DateTime, ForeignKey, Integer, Numeric
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, UUIDPrimaryKeyMixin


class UserRouteHistory(UUIDPrimaryKeyMixin, Base):
    __tablename__ = 'user_route_history'

    user_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey('users.id'), nullable=True, index=True)
    origin = mapped_column(Geometry('POINT', srid=4326), nullable=False)
    destination = mapped_column(Geometry('POINT', srid=4326), nullable=False)
    estimated_time: Mapped[int] = mapped_column(Integer, nullable=False)
    walking_distance_m: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    transfers_count: Mapped[int] = mapped_column(Integer, nullable=False)
    route_summary_json: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), nullable=False)
