from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_actor, get_db
from app.core.permissions import require_roles, resolve_role
from app.modules.admins.schemas import AdminCreateRequest, AdminUpdateRequest
from app.modules.admins.service import AdminsService
from app.shared.responses.helpers import ok

router = APIRouter(prefix='/admins', tags=['admins'])
service = AdminsService()


def _serialize(admin):
    return {
        'id': str(admin.id),
        'email': admin.email,
        'full_name': admin.full_name,
        'role': admin.role,
        'is_active': admin.is_active,
        'created_at': admin.created_at.isoformat() if admin.created_at else None,
        'updated_at': admin.updated_at.isoformat() if admin.updated_at else None,
    }


@router.get('')
def list_admins(actor=Depends(get_current_actor), db: Session = Depends(get_db)):
    require_roles(actor, {'SUPER_ADMIN'})
    admins = service.list_admins(db)
    return ok(data=[_serialize(a) for a in admins])


@router.post('')
def create_admin(payload: AdminCreateRequest, actor=Depends(get_current_actor), db: Session = Depends(get_db)):
    require_roles(actor, {'SUPER_ADMIN'})
    admin = service.create_admin(db, payload)
    return ok(data=_serialize(admin), message='Administrador creado correctamente')


@router.get('/{admin_id}')
def get_admin(admin_id: str, actor=Depends(get_current_actor), db: Session = Depends(get_db)):
    require_roles(actor, {'SUPER_ADMIN'})
    admin = service.get_admin(db, admin_id)
    return ok(data=_serialize(admin))


@router.patch('/{admin_id}')
def patch_admin(admin_id: str, payload: AdminUpdateRequest, actor=Depends(get_current_actor), db: Session = Depends(get_db)):
    require_roles(actor, {'SUPER_ADMIN'})
    admin = service.update_admin(db, admin_id, payload)
    return ok(data=_serialize(admin), message='Administrador actualizado correctamente')


@router.patch('/{admin_id}/activate')
def activate_admin(admin_id: str, actor=Depends(get_current_actor), db: Session = Depends(get_db)):
    require_roles(actor, {'SUPER_ADMIN'})
    admin = service.update_admin(db, admin_id, AdminUpdateRequest(is_active=True))
    return ok(data=_serialize(admin), message='Administrador activado correctamente')


@router.patch('/{admin_id}/deactivate')
def deactivate_admin(admin_id: str, actor=Depends(get_current_actor), db: Session = Depends(get_db)):
    require_roles(actor, {'SUPER_ADMIN'})
    admin = service.update_admin(db, admin_id, AdminUpdateRequest(is_active=False))
    return ok(data=_serialize(admin), message='Administrador desactivado correctamente')
