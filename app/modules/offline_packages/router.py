from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_actor, get_db
from app.core.permissions import require_roles
from app.modules.offline_packages.models import OfflinePackage
from app.shared.responses.helpers import ok

router = APIRouter(prefix='/offline-packages', tags=['offline_packages'])


@router.get('/latest')
def latest(db: Session = Depends(get_db)):
    row = db.scalar(select(OfflinePackage).order_by(OfflinePackage.generated_at.desc()))
    if not row:
        return ok(data={}, message='No hay paquetes')
    return ok(data={'id': str(row.id), 'version': row.version, 'status': row.status, 'file_url': row.file_url})


@router.get('/{version}/download')
def download(version: str, db: Session = Depends(get_db)):
    row = db.scalar(select(OfflinePackage).where(OfflinePackage.version == version))
    if not row:
        return ok(data={}, message='Paquete no encontrado')
    return ok(data={'version': row.version, 'file_url': row.file_url})


@router.post('/generate')
def generate(version: str, actor=Depends(get_current_actor), db: Session = Depends(get_db)):
    require_roles(actor, {'ADMIN', 'SUPER_ADMIN'})
    row = OfflinePackage(version=version, status='GENERATED', generated_at=datetime.utcnow(), package_metadata={})
    db.add(row)
    db.commit()
    return ok(data={'id': str(row.id)}, message='Paquete generado')


@router.post('/{package_id}/publish')
def publish(package_id: str, actor=Depends(get_current_actor), db: Session = Depends(get_db)):
    require_roles(actor, {'ADMIN', 'SUPER_ADMIN'})
    row = db.get(OfflinePackage, package_id)
    if not row:
        return ok(data={}, message='Paquete no encontrado')
    row.status = 'PUBLISHED'
    row.published_at = datetime.utcnow()
    db.add(row)
    db.commit()
    return ok(message='Paquete publicado')
