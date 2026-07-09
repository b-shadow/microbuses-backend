from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Linea(Base):
    __tablename__ = 'lineas'

    id_linea: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre_linea: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    color_linea: Mapped[str] = mapped_column(String(20), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    fecha_creacion: Mapped[datetime] = mapped_column(DateTime(timezone=False), server_default=func.now(), nullable=False)
