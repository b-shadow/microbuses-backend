from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_actor, get_db
from app.core.exceptions import AppException
from app.core.permissions import require_roles
from app.modules.user_history.models import UserRouteHistory
from app.modules.user_history.schemas import UserHistoryCreateRequest
from app.shared.responses.helpers import ok

router = APIRouter(prefix='/user-history', tags=['user_history'])


@router.get('')
def list_history(actor=Depends(get_current_actor), db: Session = Depends(get_db)):
    require_roles(actor, {'USER'})
    rows = db.scalars(select(UserRouteHistory).where(UserRouteHistory.user_id == actor.id).order_by(UserRouteHistory.created_at.desc())).all()
    return ok(data=[{
        'id': str(r.id),
        'estimated_time': r.estimated_time,
        'walking_distance_m': float(r.walking_distance_m),
        'transfers_count': r.transfers_count,
        'created_at': r.created_at.isoformat(),
    } for r in rows])


@router.post('')
def create_history(payload: UserHistoryCreateRequest, actor=Depends(get_current_actor), db: Session = Depends(get_db)):
    require_roles(actor, {'USER'})
    row = UserRouteHistory(
        user_id=actor.id,
        origin=f'SRID=4326;POINT({payload.origin_lng} {payload.origin_lat})',
        destination=f'SRID=4326;POINT({payload.destination_lng} {payload.destination_lat})',
        estimated_time=payload.estimated_time,
        walking_distance_m=payload.walking_distance_m,
        transfers_count=payload.transfers_count,
        route_summary_json=payload.route_summary_json,
        created_at=datetime.utcnow(),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return ok(data={'id': str(row.id)}, message='Historial guardado')


@router.delete('/{history_id}')
def delete_history(history_id: str, actor=Depends(get_current_actor), db: Session = Depends(get_db)):
    require_roles(actor, {'USER'})
    row = db.get(UserRouteHistory, history_id)
    if not row or (row.user_id and str(row.user_id) != str(actor.id)):
        raise AppException(message='Registro no encontrado', error_code='HISTORY_NOT_FOUND', status_code=404)
    db.delete(row)
    db.commit()
    return ok(message='Registro eliminado')


@router.delete('')
def clear_history(actor=Depends(get_current_actor), db: Session = Depends(get_db)):
    require_roles(actor, {'USER'})
    db.execute(delete(UserRouteHistory).where(UserRouteHistory.user_id == actor.id))
    db.commit()
    return ok(message='Historial limpiado')
