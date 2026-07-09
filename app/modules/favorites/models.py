from uuid import UUID

from geoalchemy2 import Geometry
from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, TimestampMixin, UUIDPrimaryKeyMixin


class FavoritePlace(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = 'favorite_places'

    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey('users.id'), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    location = mapped_column(Geometry('POINT', srid=4326), nullable=False)
