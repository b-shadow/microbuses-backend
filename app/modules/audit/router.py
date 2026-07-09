from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_actor, get_db
from app.core.exceptions import AppException
from app.core.permissions import require_roles, resolve_role
from app.modules.audit.models import AuditLog
from app.modules.audit.service import list_logs
from app.shared.responses.helpers import ok

router = APIRouter(prefix='/audit', tags=['audit'])


@router.get('')
def get_audit_logs(actor=Depends(get_current_actor), db: Session = Depends(get_db)):
    require_roles(actor, {'ADMIN', 'SUPER_ADMIN', 'DRIVER'})
    role = resolve_role(actor)
    logs = list_logs(db, actor_id=actor.id if role == 'DRIVER' else None)
    return ok(
        data=[
            {
                'id': str(x.id),
                'actor_id': str(x.actor_id) if x.actor_id else None,
                'actor_type': x.actor_type,
                'action': x.action,
                'entity': x.entity,
                'entity_id': str(x.entity_id) if x.entity_id else None,
                'detail': x.detail,
                'created_at': x.created_at.isoformat(),
            }
            for x in logs
        ]
    )


@router.get('/{audit_id}')
def get_audit_detail(audit_id: str, actor=Depends(get_current_actor), db: Session = Depends(get_db)):
    require_roles(actor, {'ADMIN', 'SUPER_ADMIN', 'DRIVER'})
    row = db.get(AuditLog, audit_id)
    if not row:
        return ok(data={}, message='Registro no encontrado')

    role = resolve_role(actor)
    if role == 'DRIVER' and row.actor_id != UUID(str(actor.id)):
        raise AppException(message='No autorizado', error_code='FORBIDDEN', status_code=403)

    return ok(data={'id': str(row.id), 'detail': row.detail, 'action': row.action, 'entity': row.entity})
