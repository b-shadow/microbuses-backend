from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_actor, get_db
from app.core.exceptions import AppException
from app.core.permissions import require_roles
from app.modules.active_trips.models import ActiveTrip
from app.modules.tracking.models import TrackingLocation
from app.modules.tracking.schemas import TrackingBatchRequest, TrackingLocationRequest
from app.shared.responses.helpers import ok

router = APIRouter(prefix='/tracking', tags=['tracking'])


def _validate_trip_for_driver(db: Session, active_trip_id: str, actor) -> ActiveTrip:
    trip = db.get(ActiveTrip, active_trip_id)
    if not trip or trip.status != 'ACTIVE' or str(trip.driver_id) != str(actor.id):
        raise AppException(message='Viaje activo inválido', error_code='INVALID_ACTIVE_TRIP', status_code=409)
    return trip


@router.post('/location')
def push_location(payload: TrackingLocationRequest, actor=Depends(get_current_actor), db: Session = Depends(get_db)):
    require_roles(actor, {'DRIVER'})
    trip = _validate_trip_for_driver(db, payload.active_trip_id, actor)

    row = TrackingLocation(
        active_trip_id=trip.id,
        location=f'SRID=4326;POINT({payload.lng} {payload.lat})',
        speed=payload.speed,
        recorded_at=payload.recorded_at or datetime.utcnow(),
    )
    db.add(row)
    db.commit()
    return ok(message='Ubicación registrada')


@router.post('/batch')
def push_batch(payload: TrackingBatchRequest, actor=Depends(get_current_actor), db: Session = Depends(get_db)):
    require_roles(actor, {'DRIVER'})
    trip = _validate_trip_for_driver(db, payload.active_trip_id, actor)

    if not payload.points:
        raise AppException(message='Batch vacío', error_code='EMPTY_BATCH', status_code=400)

    for p in payload.points:
        db.add(
            TrackingLocation(
                active_trip_id=trip.id,
                location=f'SRID=4326;POINT({p.lng} {p.lat})',
                speed=p.speed,
                recorded_at=p.recorded_at or datetime.utcnow(),
            )
        )
    db.commit()
    return ok(message='Batch registrado', data={'count': len(payload.points)})


@router.get('/active-buses')
def active_buses(actor=Depends(get_current_actor), db: Session = Depends(get_db)):
    require_roles(actor, {'ADMIN', 'SUPER_ADMIN'})
    trips = db.scalars(select(ActiveTrip).where(ActiveTrip.status == 'ACTIVE')).all()
    return ok(data=[{'trip_id': str(t.id), 'bus_id': str(t.bus_id), 'driver_id': str(t.driver_id), 'line_id': str(t.line_id)} for t in trips])


@router.get('/bus/{bus_id}')
def bus_tracking(bus_id: str, actor=Depends(get_current_actor), db: Session = Depends(get_db)):
    require_roles(actor, {'ADMIN', 'SUPER_ADMIN'})
    rows = db.scalars(
        select(TrackingLocation)
        .join(ActiveTrip, TrackingLocation.active_trip_id == ActiveTrip.id)
        .where(ActiveTrip.bus_id == bus_id)
        .order_by(TrackingLocation.recorded_at.desc())
        .limit(200)
    ).all()
    return ok(data=[{'id': str(x.id), 'active_trip_id': str(x.active_trip_id), 'recorded_at': x.recorded_at.isoformat(), 'speed': float(x.speed) if x.speed is not None else None} for x in rows])
