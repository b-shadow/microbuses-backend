from sqlalchemy import text
from sqlalchemy.orm import Session


def find_lines_near_point(db: Session, lat: float, lng: float, radius_m: float):
    sql = text(
        """
        SELECT DISTINCT l.id_linea, l.nombre_linea, l.color_linea
        FROM lineas l
        JOIN linea_ruta lr ON lr.id_linea = l.id_linea
        JOIN lineas_puntos lp ON lp.id_linea_ruta = lr.id_linea_ruta
        JOIN puntos p ON p.id_punto = lp.id_punto
        WHERE l.is_active = true
          AND lr.is_active = true
          AND lp.fecha_creacion IS NOT NULL
          AND ST_DWithin(
                ST_SetSRID(ST_MakePoint(p.longitud, p.latitud), 4326)::geography,
                ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography,
                :radius_m
          )
        ORDER BY l.nombre_linea
        """
    )
    rows = db.execute(sql, {'lat': lat, 'lng': lng, 'radius_m': radius_m}).mappings().all()
    return [
        {
            'id': row['id_linea'],
            'id_linea': row['id_linea'],
            'nombre_linea': row['nombre_linea'],
            'color_linea': row['color_linea'],
        }
        for row in rows
    ]
