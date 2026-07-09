from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class LineaPunto(Base):
    __tablename__ = 'lineas_puntos'
    __table_args__ = (UniqueConstraint('id_linea_ruta', 'orden', name='uq_lineas_puntos_linea_ruta_orden'),)

    id_linea_punto: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_linea_ruta: Mapped[int] = mapped_column(Integer, ForeignKey('linea_ruta.id_linea_ruta'), nullable=False, index=True)
    id_punto: Mapped[int] = mapped_column(Integer, ForeignKey('puntos.id_punto'), nullable=False)
    id_punto_dest: Mapped[int | None] = mapped_column(Integer, ForeignKey('puntos.id_punto'), nullable=True)
    orden: Mapped[int] = mapped_column(Integer, nullable=False)
    distancia: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    tiempo: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    fecha_creacion: Mapped[DateTime] = mapped_column(DateTime(timezone=False), server_default=func.now(), nullable=False)
