from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_actor, get_db
from app.core.exceptions import AppException
from app.core.permissions import require_roles
from app.modules.audit.service import log_event
from app.modules.bus_assignments.models import BusDriverAssignment
from app.modules.bus_assignments.schemas import BusAssignmentCreateRequest, BusAssignmentRemoveRequest
from app.modules.buses.models import Bus
from app.modules.drivers.models import Driver
from app.shared.responses.helpers import ok

router = APIRouter(prefix='/bus-assignments', tags=['bus_assignments'])


def _serialize(row: BusDriverAssignment):
    return {
        'id': str(row.id),
        'bus_id': str(row.bus_id),
        'driver_id': str(row.driver_id),
        'assigned_at': row.assigned_at.isoformat() if row.assigned_at else None,
        'removed_at': row.removed_at.isoformat() if row.removed_at else None,
        'is_active': row.is_active,
    }


@router.get('')
def list_assignments(actor=Depends(get_current_actor), db: Session = Depends(get_db)):
    require_roles(actor, {'ADMIN', 'SUPER_ADMIN'})
    rows = db.scalars(select(BusDriverAssignment).order_by(BusDriverAssignment.assigned_at.desc())).all()
    return ok(data=[_serialize(r) for r in rows])


@router.post('')
def create_assignment(payload: BusAssignmentCreateRequest, actor=Depends(get_current_actor), db: Session = Depends(get_db)):
    require_roles(actor, {'ADMIN', 'SUPER_ADMIN'})
    bus = db.get(Bus, payload.bus_id)
    driver = db.get(Driver, payload.driver_id)
    if not bus or not driver:
        raise AppException(message='Bus o conductor no encontrado', error_code='NOT_FOUND', status_code=404)

    exists = db.scalar(
        select(BusDriverAssignment).where(
            BusDriverAssignment.bus_id == payload.bus_id,
            BusDriverAssignment.driver_id == payload.driver_id,
            BusDriverAssignment.is_active.is_(True),
        )
    )
    if exists:
        raise AppException(message='Asignacion ya activa', error_code='ASSIGNMENT_EXISTS', status_code=409)

    row = BusDriverAssignment(
        bus_id=payload.bus_id,
        driver_id=payload.driver_id,
        assigned_at=datetime.utcnow(),
        is_active=True,
    )
    db.add(row)
    log_event(
        db,
        actor_id=getattr(actor, 'id', None),
        actor_type=actor.__class__.__name__.upper(),
        action='DRIVER_BUS_ASSIGNED',
        entity='BUS_DRIVER_ASSIGNMENT',
        entity_id=row.id,
        detail={'bus_id': payload.bus_id, 'driver_id': payload.driver_id},
    )
    db.commit()
    db.refresh(row)
    return ok(data=_serialize(row), message='Asignacion creada correctamente')


@router.delete('')
def remove_assignment(payload: BusAssignmentRemoveRequest, actor=Depends(get_current_actor), db: Session = Depends(get_db)):
    require_roles(actor, {'ADMIN', 'SUPER_ADMIN'})
    active_rows = list(
        db.scalars(
            select(BusDriverAssignment).where(
                BusDriverAssignment.bus_id == payload.bus_id,
                BusDriverAssignment.is_active.is_(True),
            )
        )
    )
    target = next((r for r in active_rows if str(r.driver_id) == payload.driver_id), None)
    if not target:
        raise AppException(message='Asignacion no encontrada', error_code='ASSIGNMENT_NOT_FOUND', status_code=404)
    if len(active_rows) <= 1:
        raise AppException(message='No se puede dejar un bus sin conductor', error_code='BUS_NEEDS_DRIVER', status_code=409)

    target.is_active = False
    target.removed_at = datetime.utcnow()
    db.add(target)
    log_event(
        db,
        actor_id=getattr(actor, 'id', None),
        actor_type=actor.__class__.__name__.upper(),
        action='DRIVER_BUS_REMOVED',
        entity='BUS_DRIVER_ASSIGNMENT',
        entity_id=target.id,
        detail={'bus_id': payload.bus_id, 'driver_id': payload.driver_id},
    )
    db.commit()
    return ok(message='Asignacion removida correctamente')
