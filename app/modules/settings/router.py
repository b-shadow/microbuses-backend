from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_actor, get_db
from app.core.permissions import require_roles
from app.modules.settings.models import Setting
from app.shared.responses.helpers import ok

router = APIRouter(prefix='/settings', tags=['settings'])


@router.get('')
def get_settings_list(db: Session = Depends(get_db)):
    rows = db.scalars(select(Setting)).all()
    return ok(data=[{'id': str(r.id), 'key': r.key, 'value': r.value, 'description': r.description} for r in rows])


@router.patch('')
def patch_settings(items: list[dict], actor=Depends(get_current_actor), db: Session = Depends(get_db)):
    require_roles(actor, {'SUPER_ADMIN'})
    for item in items:
        row = db.scalar(select(Setting).where(Setting.key == item['key']))
        if not row:
            row = Setting(key=item['key'], value=item['value'], description=item.get('description'), updated_at=datetime.utcnow())
        else:
            row.value = item['value']
            row.description = item.get('description', row.description)
            row.updated_at = datetime.utcnow()
        db.add(row)
    db.commit()
    return ok(message='Configuración actualizada')
