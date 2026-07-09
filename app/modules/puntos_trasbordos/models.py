from sqlalchemy import Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class PuntoTrasbordo(Base):
    __tablename__ = 'puntos_trasbordos'

    id_trasbordo: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_punto: Mapped[int] = mapped_column(Integer, ForeignKey('puntos.id_punto'), nullable=False, index=True)
    id_linea_origen: Mapped[int] = mapped_column(Integer, ForeignKey('lineas.id_linea'), nullable=False, index=True)
    id_linea_destino: Mapped[int] = mapped_column(Integer, ForeignKey('lineas.id_linea'), nullable=False, index=True)
    penalizacion_min: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
