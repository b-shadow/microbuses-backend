from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import AppException
from app.modules.audit.service import log_event
from app.modules.buses.models import Bus
from app.modules.buses.schemas import BusChangeLineRequest, BusCreateRequest, BusPatchRequest
from app.modules.lines.models import Linea


class BusesService:
    def _resolve_bus_status(self, line: Linea) -> str:
        if str(getattr(line, 'code', '')) == '0':
            return 'INACTIVE'
        return 'ACTIVE' if getattr(line, 'is_active', False) else 'INACTIVE'

    def list_buses(self, db: Session) -> list[Bus]:
        return db.scalars(select(Bus).order_by(Bus.created_at.desc())).all()

    def get_bus(self, db: Session, bus_id: str) -> Bus:
        bus = db.get(Bus, bus_id)
        if not bus:
            raise AppException(message='Microbus no encontrado', error_code='BUS_NOT_FOUND', status_code=404)
        return bus

    def create_bus(self, db: Session, payload: BusCreateRequest, actor):
        exists_plate = db.scalar(select(Bus).where(func.lower(Bus.plate) == payload.plate.lower()))
        if exists_plate:
            raise AppException(message='Placa ya registrada', error_code='PLATE_ALREADY_EXISTS', status_code=409)

        line = db.get(Linea, payload.current_line_id)
        if not line:
            raise AppException(message='Linea no encontrada', error_code='LINE_NOT_FOUND', status_code=404)

        bus = Bus(
            plate=payload.plate.upper(),
            model=payload.model,
            seats_count=payload.seats_count,
            internal_number=payload.internal_number,
            current_line_id=payload.current_line_id,
            photo_url=payload.photo_url,
            status=self._resolve_bus_status(line),
        )
        db.add(bus)
        db.flush()
        log_event(
            db,
            actor_id=getattr(actor, 'id', None),
            actor_type=actor.__class__.__name__.upper(),
            action='BUS_CREATED',
            entity='BUS',
            entity_id=bus.id,
            detail={'plate': bus.plate, 'line_id': str(bus.current_line_id)},
        )
        db.commit()
        db.refresh(bus)
        return bus

    def update_bus(self, db: Session, bus_id: str, payload: BusPatchRequest):
        bus = self.get_bus(db, bus_id)
        data = payload.model_dump(exclude_none=True)
        for key, value in data.items():
            setattr(bus, key, value)
        db.add(bus)
        db.commit()
        db.refresh(bus)
        return bus

    def change_line(self, db: Session, bus_id: str, payload: BusChangeLineRequest, actor):
        bus = self.get_bus(db, bus_id)
        line = db.get(Linea, payload.line_id)
        if not line:
            raise AppException(message='Linea no encontrada', error_code='LINE_NOT_FOUND', status_code=404)
        old_line = str(bus.current_line_id)
        bus.current_line_id = payload.line_id
        bus.status = self._resolve_bus_status(line)
        db.add(bus)
        log_event(
            db,
            actor_id=getattr(actor, 'id', None),
            actor_type=actor.__class__.__name__.upper(),
            action='BUS_LINE_CHANGED',
            entity='BUS',
            entity_id=bus.id,
            detail={'old_line_id': old_line, 'new_line_id': payload.line_id},
        )
        db.commit()
        db.refresh(bus)
        return bus
