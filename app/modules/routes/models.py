from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class LineaRuta(Base):
    __tablename__ = 'linea_ruta'

    id_linea_ruta: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_linea: Mapped[int] = mapped_column(Integer, ForeignKey('lineas.id_linea'), nullable=False, index=True)
    id_ruta: Mapped[int] = mapped_column(Integer, nullable=False)
    descripcion: Mapped[str] = mapped_column(String(255), nullable=False)
    distancia: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    tiempo: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    fecha_creacion: Mapped[DateTime] = mapped_column(DateTime(timezone=False), server_default=func.now(), nullable=False)
