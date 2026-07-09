from collections import defaultdict

from fastapi import APIRouter, Depends
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_actor, get_db
from app.core.permissions import require_roles
from app.modules.lines.models import Linea
from app.modules.routes.models import LineaRuta
from app.modules.routes.schemas import RouteCreateRequest, RoutePatchRequest
from app.shared.responses.helpers import ok

router = APIRouter(prefix='/linea-ruta', tags=['linea_ruta'])


@router.get('')
def list_routes(db: Session = Depends(get_db)):
    rows = db.scalars(select(LineaRuta)).all()
    return ok(
        data=[
            {
                'id_linea_ruta': row.id_linea_ruta,
                'id_linea': row.id_linea,
                'id_ruta': row.id_ruta,
                'descripcion': row.descripcion,
                'distancia': float(row.distancia) if row.distancia is not None else None,
                'tiempo': float(row.tiempo) if row.tiempo is not None else None,
                'is_active': row.is_active,
                'fecha_creacion': row.fecha_creacion.isoformat() if row.fecha_creacion else None,
            }
            for row in rows
        ]
    )


@router.post('')
def create_route(payload: RouteCreateRequest, actor=Depends(get_current_actor), db: Session = Depends(get_db)):
    require_roles(actor, {'ADMIN', 'SUPER_ADMIN'})
    line_id = payload.id_linea
    line = db.get(Linea, line_id) if line_id is not None else None
    if not line:
        return ok(data={}, message='Linea no encontrada')
    row = LineaRuta(
        id_linea=line.id_linea,
        id_ruta=payload.id_ruta or 1,
        descripcion=payload.descripcion or f'{line.nombre_linea} ruta',
        distancia=payload.distancia,
        tiempo=payload.tiempo,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return ok(data={'id_linea_ruta': row.id_linea_ruta}, message='Linea ruta creada correctamente')


@router.get('/map-lines')
def map_lines(db: Session = Depends(get_db)):
    rows = db.execute(
        text(
            """
            SELECT
                lr.id_linea_ruta,
                lr.id_ruta,
                l.id_linea,
                l.nombre_linea,
                l.color_linea,
                lp.orden,
                p1.latitud AS lat1,
                p1.longitud AS lng1,
                p2.latitud AS lat2,
                p2.longitud AS lng2
            FROM linea_ruta lr
            JOIN lineas l ON l.id_linea = lr.id_linea
            JOIN lineas_puntos lp ON lp.id_linea_ruta = lr.id_linea_ruta
            JOIN puntos p1 ON p1.id_punto = lp.id_punto
            JOIN puntos p2 ON p2.id_punto = lp.id_punto_dest
            WHERE lr.is_active = true
              AND l.is_active = true
              AND lp.fecha_creacion IS NOT NULL
            ORDER BY l.nombre_linea, lr.id_ruta, lp.orden
            """
        )
    ).mappings().all()

    grouped: dict[tuple[int, int], dict] = {}
    for row in rows:
        key = (int(row['id_linea_ruta']), int(row['id_ruta']))
        item = grouped.setdefault(
            key,
            {
                'id_linea_ruta': row['id_linea_ruta'],
                'id_ruta': row['id_ruta'],
                'id_linea': row['id_linea'],
                'nombre_linea': row['nombre_linea'],
                'color_linea': row['color_linea'],
                'geometry_geojson': {'type': 'LineString', 'coordinates': []},
            },
        )
        coordinates = item['geometry_geojson']['coordinates']
        start_point = [float(row['lng1']), float(row['lat1'])]
        end_point = [float(row['lng2']), float(row['lat2'])]
        if not coordinates:
            coordinates.append(start_point)
        if coordinates[-1] != start_point:
            coordinates.append(start_point)
        coordinates.append(end_point)

    return ok(data=list(grouped.values()))


@router.get('/by-line/{line_id}')
def get_by_line(line_id: int, db: Session = Depends(get_db)):
    rows = db.scalars(select(LineaRuta).where(LineaRuta.id_linea == line_id)).all()
    return ok(
        data=[
            {
                'id_linea_ruta': row.id_linea_ruta,
                'id_linea': row.id_linea,
                'id_ruta': row.id_ruta,
                'descripcion': row.descripcion,
                'distancia': float(row.distancia) if row.distancia is not None else None,
                'tiempo': float(row.tiempo) if row.tiempo is not None else None,
                'is_active': row.is_active,
            }
            for row in rows
        ]
    )


@router.get('/{route_id}')
def get_route(route_id: int, db: Session = Depends(get_db)):
    row = db.get(LineaRuta, route_id)
    if not row:
        return ok(data={}, message='Linea ruta no encontrada')
    return ok(
        data={
            'id_linea_ruta': row.id_linea_ruta,
            'id_linea': row.id_linea,
            'id_ruta': row.id_ruta,
            'descripcion': row.descripcion,
            'distancia': float(row.distancia) if row.distancia is not None else None,
            'tiempo': float(row.tiempo) if row.tiempo is not None else None,
            'is_active': row.is_active,
        }
    )


@router.patch('/{route_id}')
def patch_route(route_id: int, payload: RoutePatchRequest, actor=Depends(get_current_actor), db: Session = Depends(get_db)):
    require_roles(actor, {'ADMIN', 'SUPER_ADMIN'})
    row = db.get(LineaRuta, route_id)
    if not row:
        return ok(data={}, message='Linea ruta no encontrada')
    if payload.descripcion is not None:
        row.descripcion = payload.descripcion
    if payload.distancia is not None:
        row.distancia = payload.distancia
    if payload.tiempo is not None:
        row.tiempo = payload.tiempo
    if payload.is_active is not None:
        row.is_active = payload.is_active
    db.add(row)
    db.commit()
    return ok(message='Linea ruta actualizada correctamente')


@router.delete('/{route_id}')
def delete_route(route_id: int, actor=Depends(get_current_actor), db: Session = Depends(get_db)):
    require_roles(actor, {'ADMIN', 'SUPER_ADMIN'})
    row = db.get(LineaRuta, route_id)
    if not row:
        return ok(data={}, message='Linea ruta no encontrada')
    row.is_active = False
    db.add(row)
    db.commit()
    return ok(message='Linea ruta desactivada correctamente')
