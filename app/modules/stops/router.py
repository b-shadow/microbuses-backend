from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_actor, get_db
from app.core.permissions import require_roles
from app.modules.stops.models import Punto
from app.modules.stops.schemas import StopCreateRequest, StopPatchRequest
from app.shared.responses.helpers import ok

router = APIRouter(prefix='/puntos', tags=['puntos'])


@router.get('')
def list_stops(db: Session = Depends(get_db)):
    rows = db.query(Punto).all()
    return ok(
        data=[
            {
                'id_punto': punto.id_punto,
                'descripcion': punto.descripcion,
                'latitud': float(punto.latitud),
                'longitud': float(punto.longitud),
                'is_active': punto.is_active,
            }
            for punto in rows
        ]
    )


@router.post('')
def create_stop(payload: StopCreateRequest, actor=Depends(get_current_actor), db: Session = Depends(get_db)):
    require_roles(actor, {'ADMIN', 'SUPER_ADMIN'})
    descripcion = payload.descripcion or 'Punto'
    row = Punto(
        latitud=payload.latitud or 0,
        longitud=payload.longitud or 0,
        descripcion=descripcion,
        stop=payload.stop or 'N',
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return ok(data={'id': row.id_punto}, message='Punto creado correctamente')


@router.get('/{stop_id}')
def get_stop(stop_id: int, db: Session = Depends(get_db)):
    row = db.get(Punto, stop_id)
    if not row:
        return ok(data={}, message='Punto no encontrado')
    return ok(
        data={
            'id_punto': row.id_punto,
            'descripcion': row.descripcion,
            'latitud': float(row.latitud),
            'longitud': float(row.longitud),
            'is_active': row.is_active,
        }
    )


@router.patch('/{stop_id}')
def patch_stop(stop_id: int, payload: StopPatchRequest, actor=Depends(get_current_actor), db: Session = Depends(get_db)):
    require_roles(actor, {'ADMIN', 'SUPER_ADMIN'})
    row = db.get(Punto, stop_id)
    if not row:
        return ok(data={}, message='Punto no encontrado')
    if payload.descripcion is not None:
        row.descripcion = payload.descripcion
    if payload.latitud is not None:
        row.latitud = payload.latitud
    if payload.longitud is not None:
        row.longitud = payload.longitud
    if payload.stop is not None:
        row.stop = payload.stop
    if payload.is_active is not None:
        row.is_active = payload.is_active
    db.add(row)
    db.commit()
    return ok(message='Punto actualizado correctamente')


@router.delete('/{stop_id}')
def delete_stop(stop_id: int, actor=Depends(get_current_actor), db: Session = Depends(get_db)):
    require_roles(actor, {'ADMIN', 'SUPER_ADMIN'})
    row = db.get(Punto, stop_id)
    if not row:
        return ok(data={}, message='Punto no encontrado')
    row.is_active = False
    db.add(row)
    db.commit()
    return ok(message='Punto desactivado correctamente')


@router.get('/nearby')
def nearby_stops(lat: float = Query(...), lng: float = Query(...), radius_m: float = Query(300), db: Session = Depends(get_db)):
    sql = text(
        """
        SELECT
            id_punto AS id,
            descripcion,
            latitud AS lat,
            longitud AS lng,
            ST_Distance(
                ST_SetSRID(ST_MakePoint(longitud, latitud), 4326)::geography,
                ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography
            ) AS distance_m
        FROM puntos
        WHERE is_active = true
          AND ST_DWithin(
                ST_SetSRID(ST_MakePoint(longitud, latitud), 4326)::geography,
                ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography,
                :radius
          )
        ORDER BY distance_m
        LIMIT 100
        """
    )
    rows = db.execute(sql, {'lat': lat, 'lng': lng, 'radius': radius_m}).mappings().all()
    return ok(
        data=[
            {
                'id_punto': r['id'],
                'descripcion': r['descripcion'],
                'latitud': float(r['lat']),
                'longitud': float(r['lng']),
                'distance_m': float(r['distance_m']),
            }
            for r in rows
        ]
    )
