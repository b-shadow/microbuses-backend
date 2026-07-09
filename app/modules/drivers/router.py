from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_actor, get_db
from app.core.permissions import require_roles
from app.modules.drivers.schemas import DriverCreateRequest, DriverDecisionRequest, DriverUpdateRequest
from app.modules.drivers.service import DriversService
from app.shared.responses.helpers import ok

router = APIRouter(prefix='/drivers', tags=['drivers'])
service = DriversService()


def _serialize(driver):
    return {
        'id': str(driver.id),
        'email': driver.email,
        'ci': driver.ci,
        'full_name': driver.full_name,
        'approval_status': driver.approval_status,
        'phone': driver.phone,
        'license_category': driver.license_category,
        'is_active': driver.is_active,
        'created_at': driver.created_at.isoformat() if driver.created_at else None,
    }


@router.get('')
def list_drivers(
    approval_status: str | None = Query(default=None),
    actor=Depends(get_current_actor),
    db: Session = Depends(get_db),
):
    require_roles(actor, {'ADMIN', 'SUPER_ADMIN'})
    rows = service.list_drivers(db, approval_status=approval_status)
    return ok(data=[_serialize(d) for d in rows])


@router.get('/pending')
def list_pending_drivers(actor=Depends(get_current_actor), db: Session = Depends(get_db)):
    require_roles(actor, {'ADMIN', 'SUPER_ADMIN'})
    rows = service.list_drivers(db, approval_status='PENDING')
    return ok(data=[_serialize(d) for d in rows])


@router.post('')
def create_driver(payload: DriverCreateRequest, actor=Depends(get_current_actor), db: Session = Depends(get_db)):
    require_roles(actor, {'ADMIN', 'SUPER_ADMIN'})
    driver = service.create_driver(db, payload)
    return ok(data=_serialize(driver), message='Conductor creado correctamente')


@router.get('/{driver_id}')
def get_driver(driver_id: str, actor=Depends(get_current_actor), db: Session = Depends(get_db)):
    require_roles(actor, {'ADMIN', 'SUPER_ADMIN'})
    driver = service.get_driver(db, driver_id)
    return ok(data=_serialize(driver))


@router.patch('/{driver_id}')
def update_driver(driver_id: str, payload: DriverUpdateRequest, actor=Depends(get_current_actor), db: Session = Depends(get_db)):
    require_roles(actor, {'ADMIN', 'SUPER_ADMIN'})
    driver = service.update_driver(db, driver_id, payload, actor)
    return ok(data=_serialize(driver), message='Conductor actualizado correctamente')


@router.post('/{driver_id}/approve')
def approve_driver(driver_id: str, payload: DriverDecisionRequest, actor=Depends(get_current_actor), db: Session = Depends(get_db)):
    require_roles(actor, {'ADMIN', 'SUPER_ADMIN'})
    driver = service.set_status(db, driver_id, 'APPROVED', actor, payload)
    return ok(data=_serialize(driver), message='Conductor aprobado correctamente')


@router.post('/{driver_id}/reject')
def reject_driver(driver_id: str, payload: DriverDecisionRequest, actor=Depends(get_current_actor), db: Session = Depends(get_db)):
    require_roles(actor, {'ADMIN', 'SUPER_ADMIN'})
    driver = service.set_status(db, driver_id, 'REJECTED', actor, payload)
    return ok(data=_serialize(driver), message='Conductor rechazado correctamente')


@router.delete('/{driver_id}')
def delete_driver(driver_id: str, actor=Depends(get_current_actor), db: Session = Depends(get_db)):
    require_roles(actor, {'ADMIN', 'SUPER_ADMIN'})
    service.delete_driver(db, driver_id, actor)
    return ok(message='Conductor eliminado correctamente')
