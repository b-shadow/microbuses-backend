from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_actor, get_db
from app.core.exceptions import AppException
from app.core.permissions import require_roles
from app.modules.audit.service import log_event
from app.modules.buses.schemas import (
    BusAssignDriverRequest,
    BusChangeLineRequest,
    BusCreateRequest,
    BusPatchRequest,
    BusRemoveDriverRequest,
)
from app.modules.buses.service import BusesService
from app.modules.bus_assignments.models import BusDriverAssignment
from app.modules.drivers.models import Driver
from app.shared.responses.helpers import ok

router = APIRouter(prefix='/buses', tags=['buses'])
service = BusesService()


def _serialize(bus):
    return {
        'id': str(bus.id),
        'plate': bus.plate,
        'model': bus.model,
        'seats_count': bus.seats_count,
        'internal_number': bus.internal_number,
        'line_id': str(bus.current_line_id),
        'status': bus.status,
        'photo_url': bus.photo_url,
    }


@router.get('')
def list_buses(actor=Depends(get_current_actor), db: Session = Depends(get_db)):
    require_roles(actor, {'ADMIN', 'SUPER_ADMIN', 'DRIVER'})
    buses = service.list_buses(db)
    return ok(data=[_serialize(b) for b in buses])


@router.post('')
def create_bus(payload: BusCreateRequest, actor=Depends(get_current_actor), db: Session = Depends(get_db)):
    require_roles(actor, {'ADMIN', 'SUPER_ADMIN', 'DRIVER'})
    bus = service.create_bus(db, payload, actor)
    return ok(data=_serialize(bus), message='Microbus creado correctamente')


@router.get('/{bus_id}')
def get_bus(bus_id: str, actor=Depends(get_current_actor), db: Session = Depends(get_db)):
    require_roles(actor, {'ADMIN', 'SUPER_ADMIN', 'DRIVER'})
    bus = service.get_bus(db, bus_id)
    return ok(data=_serialize(bus))


@router.patch('/{bus_id}')
def patch_bus(bus_id: str, payload: BusPatchRequest, actor=Depends(get_current_actor), db: Session = Depends(get_db)):
    require_roles(actor, {'ADMIN', 'SUPER_ADMIN', 'DRIVER'})
    bus = service.update_bus(db, bus_id, payload)
    return ok(data=_serialize(bus), message='Microbus actualizado correctamente')


@router.post('/{bus_id}/change-line')
def change_line(bus_id: str, payload: BusChangeLineRequest, actor=Depends(get_current_actor), db: Session = Depends(get_db)):
    require_roles(actor, {'ADMIN', 'SUPER_ADMIN', 'DRIVER'})
    bus = service.change_line(db, bus_id, payload, actor)
    return ok(data=_serialize(bus), message='Linea cambiada correctamente')


@router.post('/{bus_id}/assign-driver')
def assign_driver(bus_id: str, payload: BusAssignDriverRequest, actor=Depends(get_current_actor), db: Session = Depends(get_db)):
    require_roles(actor, {'ADMIN', 'SUPER_ADMIN'})
    bus = service.get_bus(db, bus_id)
    driver = db.get(Driver, payload.driver_id)
    if not driver:
        raise AppException(message='Conductor no encontrado', error_code='DRIVER_NOT_FOUND', status_code=404)
    row = BusDriverAssignment(
        bus_id=bus.id,
        driver_id=driver.id,
        assigned_at=datetime.utcnow(),
        is_active=True,
    )
    db.add(row)
    log_event(db, actor_id=getattr(actor, 'id', None), actor_type=actor.__class__.__name__.upper(), action='DRIVER_BUS_ASSIGNED', entity='BUS_DRIVER_ASSIGNMENT', entity_id=row.id, detail={'bus_id': str(bus.id), 'driver_id': str(driver.id)})
    db.commit()
    return ok(message='Conductor asignado correctamente')


@router.post('/{bus_id}/remove-driver')
def remove_driver(bus_id: str, payload: BusRemoveDriverRequest, actor=Depends(get_current_actor), db: Session = Depends(get_db)):
    require_roles(actor, {'ADMIN', 'SUPER_ADMIN'})
    rows = list(db.scalars(select(BusDriverAssignment).where(BusDriverAssignment.bus_id == bus_id, BusDriverAssignment.is_active == True)))
    target = next((x for x in rows if str(x.driver_id) == payload.driver_id), None)
    if not target:
        raise AppException(message='Asignacion no encontrada', error_code='ASSIGNMENT_NOT_FOUND', status_code=404)
    if len(rows) <= 1:
        raise AppException(message='No se puede dejar un bus sin conductor', error_code='BUS_NEEDS_DRIVER', status_code=409)
    target.is_active = False
    target.removed_at = datetime.utcnow()
    db.add(target)
    log_event(db, actor_id=getattr(actor, 'id', None), actor_type=actor.__class__.__name__.upper(), action='DRIVER_BUS_REMOVED', entity='BUS_DRIVER_ASSIGNMENT', entity_id=target.id, detail={'bus_id': bus_id, 'driver_id': payload.driver_id})
    db.commit()
    return ok(message='Conductor removido correctamente')
