from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_actor, get_db
from app.core.permissions import require_roles
from app.modules.variants.models import Variant
from app.modules.variants.schemas import VariantCreateRequest, VariantPatchRequest
from app.shared.responses.helpers import ok

router = APIRouter(prefix='/variants', tags=['variants'])


@router.get('')
def list_variants(db: Session = Depends(get_db)):
    rows = db.scalars(select(Variant)).all()
    return ok(data=[{'id': str(v.id), 'line_id': str(v.line_id), 'name': v.name, 'description': v.description, 'is_active': v.is_active} for v in rows])


@router.post('')
def create_variant(payload: VariantCreateRequest, actor=Depends(get_current_actor), db: Session = Depends(get_db)):
    require_roles(actor, {'ADMIN', 'SUPER_ADMIN'})
    row = Variant(line_id=payload.line_id, name=payload.name, description=payload.description)
    db.add(row)
    db.commit()
    db.refresh(row)
    return ok(data={'id': str(row.id)}, message='Variante creada correctamente')


@router.get('/{variant_id}')
def get_variant(variant_id: str, db: Session = Depends(get_db)):
    row = db.get(Variant, variant_id)
    if not row:
        return ok(data={}, message='Variante no encontrada')
    return ok(data={'id': str(row.id), 'line_id': str(row.line_id), 'name': row.name, 'description': row.description, 'is_active': row.is_active})


@router.patch('/{variant_id}')
def patch_variant(variant_id: str, payload: VariantPatchRequest, actor=Depends(get_current_actor), db: Session = Depends(get_db)):
    require_roles(actor, {'ADMIN', 'SUPER_ADMIN'})
    row = db.get(Variant, variant_id)
    if not row:
        return ok(data={}, message='Variante no encontrada')
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(row, key, value)
    db.add(row)
    db.commit()
    return ok(message='Variante actualizada correctamente')


@router.delete('/{variant_id}')
def delete_variant(variant_id: str, actor=Depends(get_current_actor), db: Session = Depends(get_db)):
    require_roles(actor, {'ADMIN', 'SUPER_ADMIN'})
    row = db.get(Variant, variant_id)
    if not row:
        return ok(data={}, message='Variante no encontrada')
    row.is_active = False
    db.add(row)
    db.commit()
    return ok(message='Variante desactivada correctamente')
