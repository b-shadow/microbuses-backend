from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_actor, get_db
from app.core.permissions import require_roles
from app.modules.file_imports.models import FileImport
from app.shared.responses.helpers import ok

router = APIRouter(prefix='/imports', tags=['file_imports'])


@router.post('/lineas/excel')
def upload_excel(file_name: str, actor=Depends(get_current_actor), db: Session = Depends(get_db)):
    require_roles(actor, {'ADMIN', 'SUPER_ADMIN'})
    row = FileImport(file_name=file_name, status='UPLOADED', total_rows=0, valid_rows=0, invalid_rows=0, error_report=None, created_by=getattr(actor, 'id', None), created_at=datetime.utcnow(), confirmed_at=None)
    db.add(row)
    db.commit()
    return ok(data={'id': str(row.id)}, message='Archivo recibido')


@router.get('/{import_id}')
def get_import(import_id: str, actor=Depends(get_current_actor), db: Session = Depends(get_db)):
    require_roles(actor, {'ADMIN', 'SUPER_ADMIN'})
    row = db.get(FileImport, import_id)
    if not row:
        return ok(data={}, message='Importación no encontrada')
    return ok(data={'id': str(row.id), 'status': row.status, 'total_rows': row.total_rows, 'valid_rows': row.valid_rows, 'invalid_rows': row.invalid_rows})


@router.post('/{import_id}/confirm')
def confirm_import(import_id: str, actor=Depends(get_current_actor), db: Session = Depends(get_db)):
    require_roles(actor, {'ADMIN', 'SUPER_ADMIN'})
    row = db.get(FileImport, import_id)
    if not row:
        return ok(data={}, message='Importación no encontrada')
    row.status = 'CONFIRMED'
    row.confirmed_at = datetime.utcnow()
    db.add(row)
    db.commit()
    return ok(message='Importación confirmada')


@router.get('/{import_id}/errors')
def import_errors(import_id: str, actor=Depends(get_current_actor), db: Session = Depends(get_db)):
    require_roles(actor, {'ADMIN', 'SUPER_ADMIN'})
    row = db.get(FileImport, import_id)
    if not row:
        return ok(data={}, message='Importación no encontrada')
    return ok(data={'errors': row.error_report or []})
