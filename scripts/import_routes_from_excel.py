from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy import text

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.core.dependencies import SessionLocal
from app.modules.lines.models import Linea
from app.modules.puntos_trasbordos.models import PuntoTrasbordo
from app.modules.route_points.models import LineaPunto
from app.modules.routes.models import LineaRuta
from app.modules.stops.models import Punto


EXCEL_EPOCH = datetime(1899, 12, 30)
LINEA_CERO = {
    'id_linea': 0,
    'nombre_linea': '0',
    'color_linea': '#6B7280',
    'imagen_micro': None,
    'is_active': True,
}


def _to_datetime(value) -> datetime | None:
    if value in (None, ''):
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, (int, float)):
        return EXCEL_EPOCH + timedelta(days=float(value))
    return None


def _to_float(value) -> float | None:
    if value in (None, ''):
        return None
    return float(value)


def _to_int(value) -> int | None:
    if value in (None, ''):
        return None
    return int(value)


def _to_optional_dest(value) -> int | None:
    if value in (None, '', 0, '0'):
        return None
    return int(value)


def _strip(value):
    if isinstance(value, str):
        return value.strip()
    return value


def extract_workbook(xls_path: Path) -> dict[str, list[dict]]:
    ps_script = rf"""
$ErrorActionPreference = 'Stop'
$path = '{xls_path.as_posix()}'
$excel = New-Object -ComObject Excel.Application
$excel.Visible = $false
$excel.DisplayAlerts = $false
$wb = $excel.Workbooks.Open($path)
$result = [ordered]@{{}}
try {{
    foreach ($ws in $wb.Worksheets) {{
        $used = $ws.UsedRange
        $rows = $used.Rows.Count
        $cols = $used.Columns.Count
        $headers = @()
        for ($c = 1; $c -le $cols; $c++) {{
            $headers += [string]$used.Cells.Item(1, $c).Value2
        }}
        $items = @()
        for ($r = 2; $r -le $rows; $r++) {{
            $row = [ordered]@{{}}
            $empty = $true
            for ($c = 1; $c -le $cols; $c++) {{
                $key = $headers[$c - 1]
                $value = $used.Cells.Item($r, $c).Value2
                if ($null -ne $value -and $value -ne '') {{
                    $empty = $false
                }}
                $row[$key] = $value
            }}
            if (-not $empty) {{
                $items += $row
            }}
        }}
        $result[$ws.Name] = $items
    }}
}}
finally {{
    $wb.Close($false)
    $excel.Quit()
}}
$result | ConvertTo-Json -Depth 6 -Compress
"""
    completed = subprocess.run(
        ['powershell', '-NoProfile', '-Command', ps_script],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(completed.stdout)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    xls_path = repo_root / 'DatosLineas.xls'
    payload = extract_workbook(xls_path)

    lineas_rows = payload['Lineas']
    puntos_rows = payload['Puntos']
    linea_ruta_rows = payload['LineaRuta']
    lineas_puntos_rows = payload['LineasPuntos']
    puntos_trasbordos_rows = payload['PuntosTrasbordos']

    with SessionLocal() as db:
        with db.begin():
            db.execute(text('ALTER TABLE IF EXISTS lineas_puntos ALTER COLUMN id_punto_dest DROP NOT NULL'))
            db.execute(text('DELETE FROM lineas_puntos'))
            db.execute(text('DELETE FROM puntos_trasbordos'))
            db.execute(text('DELETE FROM linea_ruta'))
            db.execute(text('DELETE FROM puntos'))
            db.execute(text('DELETE FROM lineas'))

            db.execute(
                Linea.__table__.insert(),
                [
                    {
                        **LINEA_CERO,
                        'fecha_creacion': datetime.now(timezone.utc).replace(tzinfo=None),
                    }
                ]
                + [
                    {
                        'id_linea': _to_int(row['IdLinea']),
                        'nombre_linea': _strip(row['NombreLinea']),
                        'color_linea': _strip(row['ColorLinea']),
                        'imagen_micro': _strip(row['ImagenMicrobus']),
                        'is_active': True,
                        'fecha_creacion': _to_datetime(row['FechaCreacion']) or datetime.now(timezone.utc).replace(tzinfo=None),
                    }
                    for row in lineas_rows
                ],
            )
            valid_line_ids = {LINEA_CERO['id_linea']} | {
                _to_int(row['IdLinea']) for row in lineas_rows if _to_int(row['IdLinea']) is not None
            }

            db.execute(
                Punto.__table__.insert(),
                [
                    {
                        'id_punto': _to_int(row['IdPunto']),
                        'latitud': _to_float(row['Latitud']),
                        'longitud': _to_float(row['Longitud']),
                        'descripcion': _strip(row['Descripcion']),
                        'stop': _strip(row['Stop']),
                        'is_active': True,
                        'fecha_creacion': datetime.now(timezone.utc).replace(tzinfo=None),
                    }
                    for row in puntos_rows
                ],
            )

            db.execute(
                LineaRuta.__table__.insert(),
                [
                    {
                        'id_linea_ruta': _to_int(row['IdLineaRuta']),
                        'id_linea': _to_int(row['IdLinea']),
                        'id_ruta': _to_int(row['IdRuta']),
                        'descripcion': _strip(row['Descripcion']),
                        'distancia': _to_float(row['Distancia']),
                        'tiempo': _to_float(row['Tiempo']),
                        'is_active': True,
                        'fecha_creacion': datetime.now(timezone.utc).replace(tzinfo=None),
                    }
                    for row in linea_ruta_rows
                ],
            )

            db.execute(
                LineaPunto.__table__.insert(),
                [
                    {
                        'id_linea_punto': _to_int(row['IdLineaPunto']),
                        'id_linea_ruta': _to_int(row['IdLineaRuta']),
                        'id_punto': _to_int(row['IdPunto']),
                        'id_punto_dest': _to_optional_dest(row['IdPuntoDest']),
                        'orden': _to_int(row['Orden']),
                        'distancia': _to_float(row['Distancia']),
                        'tiempo': _to_float(row['Tiempo']),
                        'fecha_creacion': datetime.now(timezone.utc).replace(tzinfo=None),
                    }
                    for row in lineas_puntos_rows
                ],
            )

            db.execute(
                PuntoTrasbordo.__table__.insert(),
                [
                    {
                        'id_trasbordo': _to_int(row['IdTrasbordo']),
                        'id_punto': _to_int(row['IdPunto']),
                        'id_linea_origen': _to_int(row['IdLineaOrigen']),
                        'id_linea_destino': _to_int(row['IdLineaDestino']),
                        'penalizacion_min': _to_int(row['PenalizacionMin']) or 5,
                    }
                    for row in puntos_trasbordos_rows
                    if _to_int(row['IdLineaOrigen']) in valid_line_ids
                    and _to_int(row['IdLineaDestino']) in valid_line_ids
                ],
            )

            for table, column in [
                ('lineas', 'id_linea'),
                ('puntos', 'id_punto'),
                ('linea_ruta', 'id_linea_ruta'),
                ('lineas_puntos', 'id_linea_punto'),
                ('puntos_trasbordos', 'id_trasbordo'),
            ]:
                db.execute(
                    text(
                        f"""
                        SELECT setval(
                            pg_get_serial_sequence(:table_name, :column_name),
                            COALESCE((SELECT MAX({column}) FROM {table}), 1),
                            true
                        )
                        """
                    ),
                    {'table_name': table, 'column_name': column},
                )

    print('Importación completada.')


if __name__ == '__main__':
    main()
