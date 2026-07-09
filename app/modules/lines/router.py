from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_actor, get_db
from app.core.permissions import require_roles
from app.modules.lines.models import Linea
from app.modules.lines.schemas import LineCreateRequest, LinePatchRequest
from app.shared.responses.helpers import ok

router = APIRouter(prefix='/lineas', tags=['lineas'])


@router.get('')
def list_lines(db: Session = Depends(get_db)):
    lines = db.scalars(select(Linea)).all()
    return ok(
        data=[
            {
                'id_linea': line.id_linea,
                'nombre_linea': line.nombre_linea,
                'color_linea': line.color_linea,
                'is_active': line.is_active,
                'fecha_creacion': line.fecha_creacion.isoformat() if line.fecha_creacion else None,
            }
            for line in lines
        ]
    )


@router.post('')
def create_line(payload: LineCreateRequest, actor=Depends(get_current_actor), db: Session = Depends(get_db)):
    require_roles(actor, {'ADMIN', 'SUPER_ADMIN'})
    line = Linea(
        nombre_linea=payload.nombre_linea,
        color_linea=payload.color_linea or '#000000',
    )
    db.add(line)
    db.commit()
    db.refresh(line)
    return ok(data={'id_linea': line.id_linea}, message='Linea creada correctamente')


@router.get('/{line_id}')
def get_line(line_id: int, db: Session = Depends(get_db)):
    line = db.get(Linea, line_id)
    if not line:
        return ok(data={}, message='Linea no encontrada')
    return ok(
        data={
            'id_linea': line.id_linea,
            'nombre_linea': line.nombre_linea,
            'color_linea': line.color_linea,
            'is_active': line.is_active,
        }
    )


@router.patch('/{line_id}')
def patch_line(line_id: int, payload: LinePatchRequest, actor=Depends(get_current_actor), db: Session = Depends(get_db)):
    require_roles(actor, {'ADMIN', 'SUPER_ADMIN'})
    line = db.get(Linea, line_id)
    if not line:
        return ok(data={}, message='Linea no encontrada')
    if payload.nombre_linea is not None:
        line.nombre_linea = payload.nombre_linea
    if payload.color_linea is not None:
        line.color_linea = payload.color_linea
    if payload.is_active is not None:
        line.is_active = payload.is_active
    db.add(line)
    db.commit()
    return ok(message='Linea actualizada correctamente')


@router.delete('/{line_id}')
def delete_line(line_id: int, actor=Depends(get_current_actor), db: Session = Depends(get_db)):
    require_roles(actor, {'ADMIN', 'SUPER_ADMIN'})
    line = db.get(Linea, line_id)
    if not line:
        return ok(data={}, message='Linea no encontrada')
    line.is_active = False
    db.add(line)
    db.commit()
    return ok(message='Linea desactivada correctamente')
