from datetime import datetime
from typing import Optional

from sqlalchemy import BIGINT, DateTime, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, UUIDPrimaryKeyMixin


class OfflinePackage(UUIDPrimaryKeyMixin, Base):
    __tablename__ = 'offline_packages'

    version: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    file_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    file_size_bytes: Mapped[Optional[int]] = mapped_column(BIGINT, nullable=True)
    package_metadata: Mapped[Optional[dict]] = mapped_column('metadata', JSONB, nullable=True)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), nullable=False)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=False), nullable=True)
