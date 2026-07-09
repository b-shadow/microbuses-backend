from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_actor, get_db
from app.core.permissions import require_roles
from app.modules.route_points.models import LineaPunto
from app.modules.route_points.schemas import (
    RoutePointCreateRequest,
    RoutePointPatchRequest,
    RoutePointReorderRequest,
)
from app.modules.stops.models import Punto
from app.shared.responses.helpers import ok

router = APIRouter(prefix='/lineas-puntos', tags=['lineas_puntos'])


@router.get('')
def list_points(db: Session = Depends(get_db)):
    rows = db.scalars(select(LineaPunto).order_by(LineaPunto.id_linea_ruta, LineaPunto.orden)).all()
    point_cache = {}
    return ok(
        data=[
            {
                'id_linea_punto': point.id_linea_punto,
                'id_linea_ruta': point.id_linea_ruta,
                'id_punto': point.id_punto,
                'id_punto_dest': point.id_punto_dest,
                'orden': point.orden,
                'distancia': float(point.distancia) if point.distancia is not None else None,
                'tiempo': float(point.tiempo) if point.tiempo is not None else None,
            }
            for point in rows
        ]
    )


@router.post('')
def create_point(payload: RoutePointCreateRequest, actor=Depends(get_current_actor), db: Session = Depends(get_db)):
    require_roles(actor, {'ADMIN', 'SUPER_ADMIN'})
    linea_ruta_id = payload.id_linea_ruta
    if linea_ruta_id is None:
        return ok(data={}, message='Linea ruta no encontrada')
    orden = payload.orden or 1
    if payload.id_punto is None:
        return ok(data={}, message='Punto no encontrado')
    row = LineaPunto(
        id_linea_ruta=linea_ruta_id,
        id_punto=payload.id_punto,
        id_punto_dest=payload.id_punto_dest or payload.id_punto,
        orden=orden,
        distancia=payload.distancia,
        tiempo=payload.tiempo,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return ok(data={'id_linea_punto': row.id_linea_punto}, message='Linea punto creada correctamente')


@router.patch('/{point_id}')
def patch_point(point_id: int, payload: RoutePointPatchRequest, actor=Depends(get_current_actor), db: Session = Depends(get_db)):
    require_roles(actor, {'ADMIN', 'SUPER_ADMIN'})
    row = db.get(LineaPunto, point_id)
    if not row:
        return ok(data={}, message='Linea punto no encontrada')
    if payload.orden is not None:
        row.orden = payload.orden
    if payload.id_punto is not None:
        row.id_punto = payload.id_punto
    if payload.id_punto_dest is not None:
        row.id_punto_dest = payload.id_punto_dest
    if payload.distancia is not None:
        row.distancia = payload.distancia
    if payload.tiempo is not None:
        row.tiempo = payload.tiempo
    db.add(row)
    db.commit()
    return ok(message='Linea punto actualizada correctamente')


@router.delete('/{point_id}')
def delete_point(point_id: int, actor=Depends(get_current_actor), db: Session = Depends(get_db)):
    require_roles(actor, {'ADMIN', 'SUPER_ADMIN'})
    row = db.get(LineaPunto, point_id)
    if not row:
        return ok(data={}, message='Linea punto no encontrada')
    db.delete(row)
    db.commit()
    return ok(message='Linea punto eliminada correctamente')


@router.post('/reorder')
def reorder(payload: RoutePointReorderRequest, actor=Depends(get_current_actor), db: Session = Depends(get_db)):
    require_roles(actor, {'ADMIN', 'SUPER_ADMIN'})
    for item in payload.points:
        row = db.get(LineaPunto, item.id)
        if row:
            row.orden = item.orden
            db.add(row)
    db.commit()
    return ok(message='Orden actualizado correctamente')
