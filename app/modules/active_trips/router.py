from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_actor, get_db
from app.core.exceptions import AppException
from app.core.permissions import require_roles
from app.modules.active_trips.models import ActiveTrip
from app.modules.active_trips.schemas import StartTripRequest
from app.modules.audit.service import log_event
from app.modules.drivers.models import Driver
from app.shared.responses.helpers import ok

router = APIRouter(prefix='/active-trips', tags=['active_trips'])


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _iso_utc(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat()


@router.post('/start')
def start_trip(payload: StartTripRequest, actor=Depends(get_current_actor), db: Session = Depends(get_db)):
    require_roles(actor, {'DRIVER'})
    if actor.approval_status != 'APPROVED':
        raise AppException(message='Conductor no aprobado', error_code='DRIVER_NOT_APPROVED', status_code=403)

    current = db.scalar(select(ActiveTrip).where(ActiveTrip.driver_id == actor.id, ActiveTrip.status == 'ACTIVE'))
    if current:
        raise AppException(message='Ya existe un viaje activo', error_code='ACTIVE_TRIP_EXISTS', status_code=409)

    row = ActiveTrip(
        driver_id=actor.id,
        bus_id=payload.bus_id,
        line_id=payload.line_id,
        route_id=payload.route_id,
        started_at=_utcnow(),
        status='ACTIVE',
        created_at=_utcnow(),
    )
    db.add(row)
    db.flush()
    log_event(db, actor_id=actor.id, actor_type='DRIVER', action='TRIP_STARTED', entity='ACTIVE_TRIP', entity_id=row.id)
    db.commit()
    return ok(
        data={
            'id': str(row.id),
            'started_at': _iso_utc(row.started_at),
            'bus_id': str(row.bus_id),
            'line_id': row.line_id,
            'status': row.status,
        },
        message='Viaje iniciado correctamente',
    )


@router.post('/{trip_id}/finish')
def finish_trip(trip_id: str, actor=Depends(get_current_actor), db: Session = Depends(get_db)):
    require_roles(actor, {'DRIVER'})
    row = db.get(ActiveTrip, trip_id)
    if not row or str(row.driver_id) != str(actor.id):
        raise AppException(message='Viaje no encontrado', error_code='TRIP_NOT_FOUND', status_code=404)
    if row.status != 'ACTIVE':
        raise AppException(message='El viaje ya fue finalizado', error_code='TRIP_ALREADY_FINISHED', status_code=409)

    row.status = 'FINISHED'
    row.finished_at = _utcnow()
    db.add(row)
    log_event(db, actor_id=actor.id, actor_type='DRIVER', action='TRIP_FINISHED', entity='ACTIVE_TRIP', entity_id=row.id)
    db.commit()
    return ok(
        data={
            'id': str(row.id),
            'started_at': _iso_utc(row.started_at),
            'finished_at': _iso_utc(row.finished_at),
            'bus_id': str(row.bus_id),
            'line_id': row.line_id,
            'status': row.status,
        },
        message='Viaje finalizado correctamente',
    )


@router.get('/current')
def current_trip(actor=Depends(get_current_actor), db: Session = Depends(get_db)):
    require_roles(actor, {'DRIVER'})
    row = db.scalar(select(ActiveTrip).where(ActiveTrip.driver_id == actor.id, ActiveTrip.status == 'ACTIVE'))
    if not row:
        return ok(data={}, message='Sin viaje activo')
    return ok(
        data={
            'id': str(row.id),
            'started_at': _iso_utc(row.started_at),
            'bus_id': str(row.bus_id),
            'line_id': row.line_id,
            'status': row.status,
        }
    )


@router.get('/history')
def trip_history(actor=Depends(get_current_actor), db: Session = Depends(get_db)):
    require_roles(actor, {'DRIVER', 'ADMIN', 'SUPER_ADMIN'})
    if isinstance(actor, Driver):
        rows = db.scalars(select(ActiveTrip).where(ActiveTrip.driver_id == actor.id).order_by(ActiveTrip.started_at.desc())).all()
    else:
        rows = db.scalars(select(ActiveTrip).order_by(ActiveTrip.started_at.desc())).all()
    return ok(
        data=[
            {
                'id': str(r.id),
                'driver_id': str(r.driver_id),
                'bus_id': str(r.bus_id),
                'line_id': r.line_id,
                'status': r.status,
                'started_at': _iso_utc(r.started_at),
                'finished_at': _iso_utc(r.finished_at),
            }
            for r in rows
        ]
    )
