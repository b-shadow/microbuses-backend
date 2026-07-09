from sqlalchemy import Boolean, DateTime, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Punto(Base):
    __tablename__ = 'puntos'

    id_punto: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    latitud: Mapped[float] = mapped_column(Numeric(10, 6), nullable=False)
    longitud: Mapped[float] = mapped_column(Numeric(10, 6), nullable=False)
    descripcion: Mapped[str] = mapped_column(String(120), nullable=False)
    stop: Mapped[str] = mapped_column(String(1), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    fecha_creacion: Mapped[DateTime] = mapped_column(DateTime(timezone=False), server_default=func.now(), nullable=False)
