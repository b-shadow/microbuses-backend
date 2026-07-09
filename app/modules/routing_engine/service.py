from __future__ import annotations

from dataclasses import dataclass
from heapq import heappop, heappush
from math import atan2, cos, radians, sin, sqrt
from itertools import count

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.modules.walking_network.service import WalkingNetworkService, WalkingPathResult


@dataclass
class RoutePoint:
    lat: float
    lng: float
    point_id: int | None = None
    stop: str | None = None


@dataclass
class RoutePosition:
    segment_index: int
    offset: float
    lat: float
    lng: float
    straight_distance_m: float

    @property
    def scalar(self) -> float:
        return self.segment_index + self.offset


@dataclass
class RouteData:
    route_id: int
    line_id: int
    line_name: str
    line_color: str
    points: list[RoutePoint]
    segment_distances: list[float]
    segment_minutes: list[float]

    @property
    def last_index(self) -> int:
        return len(self.points) - 1

    @property
    def segment_count(self) -> int:
        return len(self.segment_minutes)

    @property
    def is_circular(self) -> bool:
        if len(self.points) < 3:
            return False
        return haversine_m(
            self.points[0].lat,
            self.points[0].lng,
            self.points[-1].lat,
            self.points[-1].lng,
        ) <= 250.0

    def _project_to_segment(self, lat: float, lng: float, start: RoutePoint, end: RoutePoint) -> tuple[float, float, float]:
        ax = start.lng
        ay = start.lat
        bx = end.lng
        by = end.lat
        apx = lng - ax
        apy = lat - ay
        abx = bx - ax
        aby = by - ay
        ab_len_sq = abx * abx + aby * aby
        if ab_len_sq == 0:
            return 0.0, ay, ax
        t = max(0.0, min(1.0, (apx * abx + apy * aby) / ab_len_sq))
        projected_lng = ax + (abx * t)
        projected_lat = ay + (aby * t)
        return t, projected_lat, projected_lng

    def nearest_point_index(self, lat: float, lng: float, allowed_stop_only: bool = False) -> tuple[int, float] | None:
        best_index = -1
        best_distance = float('inf')
        for index, point in enumerate(self.points):
            if allowed_stop_only and (point.stop or '').strip().upper() != 'S':
                continue
            distance = haversine_m(lat, lng, point.lat, point.lng)
            if distance < best_distance:
                best_distance = distance
                best_index = index
        if best_index < 0:
            return None
        return best_index, best_distance

    def nearest_position(self, lat: float, lng: float) -> RoutePosition | None:
        if len(self.points) < 2:
            return None
        best: RoutePosition | None = None
        for segment_index in range(len(self.points) - 1):
            start = self.points[segment_index]
            end = self.points[segment_index + 1]
            offset, projected_lat, projected_lng = self._project_to_segment(lat, lng, start, end)
            distance = haversine_m(lat, lng, projected_lat, projected_lng)
            if best is None or distance < best.straight_distance_m:
                best = RoutePosition(
                    segment_index=segment_index,
                    offset=offset,
                    lat=projected_lat,
                    lng=projected_lng,
                    straight_distance_m=distance,
                )
        return best

    def position_at_point_index(self, index: int) -> RoutePosition | None:
        if not self.points:
            return None
        clamped_index = max(0, min(index, self.last_index))
        point = self.points[clamped_index]
        if clamped_index >= self.last_index:
            if self.segment_count == 0:
                segment_index = 0
                offset = 0.0
            else:
                segment_index = self.last_index - 1
                offset = 1.0
        else:
            segment_index = clamped_index
            offset = 0.0
        return RoutePosition(
            segment_index=segment_index,
            offset=offset,
            lat=point.lat,
            lng=point.lng,
            straight_distance_m=0.0,
        )

    def nearest_stop_position(self, lat: float, lng: float) -> RoutePosition | None:
        nearest = self.nearest_point_index(lat, lng, allowed_stop_only=True)
        if nearest is None:
            return None
        index, distance = nearest
        position = self.position_at_point_index(index)
        if position is None:
            return None
        position.straight_distance_m = distance
        return position

    def position_for_point_id(self, point_id: int, *, stop_only: bool = False) -> RoutePosition | None:
        for index, point in enumerate(self.points):
            if point.point_id != point_id:
                continue
            if stop_only and (point.stop or '').strip().upper() != 'S':
                continue
            return self.position_at_point_index(index)
        return None

    def partial_minutes(self, from_index: int, to_index: int) -> float:
        if to_index <= from_index:
            return 0.0
        return sum(self.segment_minutes[from_index:to_index])

    def partial_distance(self, from_index: int, to_index: int) -> float:
        if to_index <= from_index:
            return 0.0
        return sum(self.segment_distances[from_index:to_index])

    def geometry_slice(self, from_index: int, to_index: int) -> list[dict]:
        if to_index <= from_index:
            return []
        return [{'lat': point.lat, 'lng': point.lng} for point in self.points[from_index : to_index + 1]]

    def _effective_end_scalar(self, start: RoutePosition, end: RoutePosition) -> float:
        end_scalar = end.scalar
        if self.is_circular and end_scalar <= start.scalar:
            end_scalar += self.segment_count
        return end_scalar

    def _point_from_scalar_value(self, scalar: float) -> dict:
        if self.segment_count == 0:
            point = self.points[0]
            return {'lat': point.lat, 'lng': point.lng}

        if self.is_circular:
            normalized = scalar % self.segment_count
        else:
            normalized = max(0.0, min(float(self.segment_count), scalar))

        if normalized == self.segment_count:
            point = self.points[-1]
            return {'lat': point.lat, 'lng': point.lng}

        segment_index = min(int(normalized), self.segment_count - 1)
        offset = normalized - int(normalized)
        start = self.points[segment_index]
        end = self.points[segment_index + 1]
        return {
            'lat': start.lat + ((end.lat - start.lat) * offset),
            'lng': start.lng + ((end.lng - start.lng) * offset),
        }

    def partial_minutes_position(self, start: RoutePosition, end: RoutePosition) -> float:
        end_scalar = self._effective_end_scalar(start, end)
        if end_scalar <= start.scalar:
            return 0.0
        total = 0.0
        current_scalar = start.scalar
        while current_scalar < end_scalar:
            integer_part = int(current_scalar)
            segment_index = integer_part % self.segment_count
            next_scalar = min(float(integer_part + 1), end_scalar)
            total += self.segment_minutes[segment_index] * (next_scalar - current_scalar)
            current_scalar = next_scalar
        return total

    def partial_distance_position(self, start: RoutePosition, end: RoutePosition) -> float:
        end_scalar = self._effective_end_scalar(start, end)
        if end_scalar <= start.scalar:
            return 0.0
        total = 0.0
        current_scalar = start.scalar
        while current_scalar < end_scalar:
            integer_part = int(current_scalar)
            segment_index = integer_part % self.segment_count
            next_scalar = min(float(integer_part + 1), end_scalar)
            total += self.segment_distances[segment_index] * (next_scalar - current_scalar)
            current_scalar = next_scalar
        return total

    def geometry_between_positions(self, start: RoutePosition, end: RoutePosition) -> list[dict]:
        end_scalar = self._effective_end_scalar(start, end)
        if end_scalar <= start.scalar:
            return []
        geometry = [{'lat': start.lat, 'lng': start.lng}]
        current_integer = int(start.scalar) + 1
        while current_integer <= int(end_scalar):
            boundary_point = self._point_from_scalar_value(float(current_integer))
            if geometry[-1] != boundary_point:
                geometry.append(boundary_point)
            current_integer += 1
        end_point = self._point_from_scalar_value(end_scalar)
        if geometry[-1] != end_point:
            geometry.append(end_point)
        return geometry

    def position_from_scalar(self, scalar: float) -> RoutePosition:
        segment_index = min(int(scalar), self.last_index - 1)
        offset = max(0.0, min(1.0, scalar - segment_index))
        start = self.points[segment_index]
        end = self.points[segment_index + 1]
        lat = start.lat + ((end.lat - start.lat) * offset)
        lng = start.lng + ((end.lng - start.lng) * offset)
        return RoutePosition(
            segment_index=segment_index,
            offset=offset,
            lat=lat,
            lng=lng,
            straight_distance_m=0.0,
        )


@dataclass
class CandidatePoint:
    route_id: int
    line_id: int
    line_name: str
    line_color: str
    position: RoutePosition
    walk: WalkingPathResult


@dataclass
class TransferOption:
    transfer_id: int
    point_id: int
    source_line_id: int
    destination_line_id: int
    penalty_minutes: float
    lat: float
    lng: float


@dataclass
class DynamicTransferOption:
    source_route_id: int
    source_line_id: int
    target_route_id: int
    target_line_id: int
    source_position: RoutePosition
    target_position: RoutePosition
    estimated_distance_m: float
    estimated_minutes: int


def haversine_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    r = 6371000.0
    dlat = radians(lat2 - lat1)
    dlng = radians(lng2 - lng1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlng / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return r * c


class RoutingEngineService:
    def __init__(self) -> None:
        self.walking_network_service = WalkingNetworkService()
        self.max_route_results = 8
        self.max_candidate_points = 12
        self.max_candidates_per_route = 2
        self.dynamic_transfer_point_stride = 6

    def _estimated_bus_minutes(self, distance_m: float, raw_minutes: float) -> float:
        if raw_minutes > 0:
            return raw_minutes
        if distance_m <= 0:
            return 0.0
        default_bus_speed_kmh = 18.0
        return distance_m / (default_bus_speed_kmh * 1000 / 60)

    def _load_routes(self, db: Session) -> tuple[dict[int, RouteData], dict[int, list[int]]]:
        sql = text(
            """
            SELECT
                lr.id_linea_ruta AS route_id,
                lr.id_linea AS line_id,
                l.nombre_linea AS line_name,
                l.color_linea AS line_color,
                lp.orden,
                COALESCE(lp.distancia, 0) AS segment_distance_m,
                COALESCE(lp.tiempo, 0) AS segment_minutes,
                p1.id_punto AS point_id1,
                p1.latitud AS lat1,
                p1.longitud AS lng1,
                p1.stop AS stop1,
                p2.id_punto AS point_id2,
                p2.latitud AS lat2,
                p2.longitud AS lng2,
                p2.stop AS stop2
            FROM linea_ruta lr
            JOIN lineas l ON l.id_linea = lr.id_linea
            JOIN lineas_puntos lp ON lp.id_linea_ruta = lr.id_linea_ruta
            JOIN puntos p1 ON p1.id_punto = lp.id_punto
            JOIN puntos p2 ON p2.id_punto = lp.id_punto_dest
            WHERE lr.is_active = true
              AND l.is_active = true
              AND lp.id_punto_dest IS NOT NULL
            ORDER BY lr.id_linea_ruta, lp.orden
            """
        )
        rows = db.execute(sql).mappings().all()
        routes: dict[int, RouteData] = {}
        routes_by_line: dict[int, list[int]] = {}

        for row in rows:
            route_id = int(row['route_id'])
            line_id = int(row['line_id'])
            route = routes.get(route_id)
            if route is None:
                route = RouteData(
                    route_id=route_id,
                    line_id=line_id,
                    line_name=str(row['line_name']),
                    line_color=str(row['line_color'] or '#FF0000'),
                    points=[],
                    segment_distances=[],
                    segment_minutes=[],
                )
                routes[route_id] = route
                routes_by_line.setdefault(line_id, []).append(route_id)

            start_point = RoutePoint(
                lat=float(row['lat1']),
                lng=float(row['lng1']),
                point_id=int(row['point_id1']) if row['point_id1'] is not None else None,
                stop=str(row['stop1']) if row['stop1'] is not None else None,
            )
            end_point = RoutePoint(
                lat=float(row['lat2']),
                lng=float(row['lng2']),
                point_id=int(row['point_id2']) if row['point_id2'] is not None else None,
                stop=str(row['stop2']) if row['stop2'] is not None else None,
            )

            if not route.points:
                route.points.append(start_point)
            last_point = route.points[-1]
            if last_point.lat != start_point.lat or last_point.lng != start_point.lng:
                route.points.append(start_point)
            route.points.append(end_point)
            segment_distance = float(row['segment_distance_m'] or 0.0)
            segment_minutes = float(row['segment_minutes'] or 0.0)
            route.segment_distances.append(segment_distance)
            route.segment_minutes.append(self._estimated_bus_minutes(segment_distance, segment_minutes))

        cleaned_routes = {
            route_id: route
            for route_id, route in routes.items()
            if len(route.points) >= 2 and len(route.segment_minutes) == len(route.points) - 1
        }
        cleaned_by_line = {
            line_id: [route_id for route_id in route_ids if route_id in cleaned_routes]
            for line_id, route_ids in routes_by_line.items()
        }
        return cleaned_routes, cleaned_by_line

    def _load_transfers(self, db: Session) -> list[TransferOption]:
        sql = text(
            """
            SELECT
                pt.id_trasbordo,
                pt.id_punto,
                pt.id_linea_origen,
                pt.id_linea_destino,
                pt.penalizacion_min,
                p.latitud,
                p.longitud
            FROM puntos_trasbordos pt
            JOIN puntos p ON p.id_punto = pt.id_punto
            """
        )
        rows = db.execute(sql).mappings().all()
        return [
            TransferOption(
                transfer_id=int(row['id_trasbordo']),
                point_id=int(row['id_punto']),
                source_line_id=int(row['id_linea_origen']),
                destination_line_id=int(row['id_linea_destino']),
                penalty_minutes=float(row['penalizacion_min'] or 5),
                lat=float(row['latitud']),
                lng=float(row['longitud']),
            )
            for row in rows
        ]

    def _walk_between(
        self,
        from_lat: float,
        from_lng: float,
        to_lat: float,
        to_lng: float,
        *,
        allow_straight_fallback: bool = False,
    ) -> WalkingPathResult | None:
        return self.walking_network_service.route(
            origin_lat=from_lat,
            origin_lng=from_lng,
            destination_lat=to_lat,
            destination_lng=to_lng,
            allow_straight_fallback=allow_straight_fallback,
        )

    def _estimated_walk_minutes(self, distance_m: float) -> int:
        speed_kmh = self.walking_network_service.settings.walking_default_speed_kmh
        if distance_m <= 0:
            return 0
        minutes = distance_m / (speed_kmh * 1000 / 60)
        return max(1, int(round(minutes)))

    def preload_walking_graph(self) -> bool:
        return self.walking_network_service.preload_graph()

    def _candidate_positions_for_route(
        self,
        *,
        route: RouteData,
        lat: float,
        lng: float,
        max_walk_m: float,
        boarding_mode: str,
    ) -> list[tuple[float, RoutePosition]]:
        stop_only = boarding_mode == 'STOPS_ONLY'
        positions: list[tuple[float, RoutePosition]] = []

        if stop_only:
            stop_candidates: list[tuple[float, int]] = []
            for index, point in enumerate(route.points):
                if (point.stop or '').strip().upper() != 'S':
                    continue
                distance = haversine_m(lat, lng, point.lat, point.lng)
                if distance <= max_walk_m:
                    stop_candidates.append((distance, index))
            stop_candidates.sort(key=lambda item: item[0])
            for distance, index in stop_candidates[: self.max_candidates_per_route]:
                position = route.position_at_point_index(index)
                if position is None:
                    continue
                position.straight_distance_m = distance
                positions.append(
                    (
                        distance,
                        position,
                    )
                )
            return positions

        nearest = route.nearest_position(lat, lng)
        if nearest is not None and nearest.straight_distance_m <= max_walk_m:
            positions.append((nearest.straight_distance_m, nearest))

        point_candidates: list[tuple[float, int]] = []
        for index, point in enumerate(route.points[:-1]):
            distance = haversine_m(lat, lng, point.lat, point.lng)
            if distance <= max_walk_m:
                point_candidates.append((distance, index))
        point_candidates.sort(key=lambda item: item[0])

        for distance, index in point_candidates[: self.max_candidates_per_route + 1]:
            point = route.points[index]
            candidate = RoutePosition(
                segment_index=index,
                offset=0.0,
                lat=point.lat,
                lng=point.lng,
                straight_distance_m=distance,
            )
            positions.append((distance, candidate))

        deduped: list[tuple[float, RoutePosition]] = []
        seen_scalars: set[int] = set()
        for distance, position in sorted(positions, key=lambda item: item[0]):
            scalar_key = int(round(position.scalar * 100))
            if scalar_key in seen_scalars:
                continue
            seen_scalars.add(scalar_key)
            deduped.append((distance, position))
            if len(deduped) >= self.max_candidates_per_route:
                break
        return deduped

    def _candidate_points(
        self,
        *,
        routes: dict[int, RouteData],
        lat: float,
        lng: float,
        max_walk_m: float,
        boarding_mode: str,
        walk_cache: dict[tuple[float, float, float, float], WalkingPathResult | None],
        limit: int | None = None,
    ) -> dict[int, list[CandidatePoint]]:
        rough: list[tuple[float, int, RoutePosition]] = []

        for route_id, route in routes.items():
            for straight_distance, position in self._candidate_positions_for_route(
                route=route,
                lat=lat,
                lng=lng,
                max_walk_m=max_walk_m,
                boarding_mode=boarding_mode,
            ):
                rough.append((straight_distance, route_id, position))

        rough.sort(key=lambda item: item[0])
        selected: dict[int, list[CandidatePoint]] = {}
        limit = limit or self.max_candidate_points

        for _, route_id, position in rough[:limit]:
            walk_key = (
                round(lat, 6),
                round(lng, 6),
                round(position.lat, 6),
                round(position.lng, 6),
            )
            if walk_key not in walk_cache:
                walk_cache[walk_key] = self._walk_between(
                    lat,
                    lng,
                    position.lat,
                    position.lng,
                    allow_straight_fallback=False,
                )
            walk = walk_cache[walk_key]
            if walk is None or walk.distance_m > max_walk_m:
                continue
            route = routes[route_id]
            route_candidates = selected.setdefault(route_id, [])
            scalar_key = int(round(position.scalar * 100))
            if any(int(round(item.position.scalar * 100)) == scalar_key for item in route_candidates):
                continue
            route_candidates.append(CandidatePoint(
                route_id=route_id,
                line_id=route.line_id,
                line_name=route.line_name,
                line_color=route.line_color,
                position=position,
                walk=walk,
            ))
            if len(route_candidates) > self.max_candidates_per_route:
                route_candidates.sort(key=lambda item: item.walk.estimated_minutes)
                del route_candidates[self.max_candidates_per_route :]
        return selected

    def _build_dynamic_transfers(
        self,
        *,
        routes: dict[int, RouteData],
        max_walk_m: float,
        stop_only: bool = False,
    ) -> dict[int, list[DynamicTransferOption]]:
        route_ids = sorted(routes.keys())
        dynamic_by_source: dict[int, list[DynamicTransferOption]] = {}

        for source_route_id in route_ids:
            source_route = routes[source_route_id]
            for target_route_id in route_ids:
                if source_route_id == target_route_id:
                    continue
                target_route = routes[target_route_id]
                if source_route.line_id == target_route.line_id:
                    continue

                best_source_position: RoutePosition | None = None
                best_target_position: RoutePosition | None = None
                best_straight_distance = float('inf')

                source_points = list(enumerate(source_route.points))
                if stop_only:
                    source_points = [
                        (index, point)
                        for index, point in source_points
                        if (point.stop or '').strip().upper() == 'S'
                    ]
                sampled_points = source_points[:: self.dynamic_transfer_point_stride]
                if sampled_points:
                    last_index = len(source_route.points) - 1
                    if sampled_points[-1][0] != last_index:
                        sampled_points.append((last_index, source_route.points[last_index]))

                for point_index, source_point in sampled_points:
                    if stop_only:
                        target_position = target_route.nearest_stop_position(source_point.lat, source_point.lng)
                    else:
                        target_position = target_route.nearest_position(source_point.lat, source_point.lng)
                    if target_position is None:
                        continue
                    straight_distance = haversine_m(
                        source_point.lat,
                        source_point.lng,
                        target_position.lat,
                        target_position.lng,
                    )
                    if straight_distance > max_walk_m or straight_distance >= best_straight_distance:
                        continue
                    best_straight_distance = straight_distance
                    best_source_position = source_route.position_at_point_index(point_index)
                    if best_source_position is None:
                        continue
                    best_target_position = target_position

                if best_source_position is None or best_target_position is None:
                    continue

                dynamic_by_source.setdefault(source_route_id, []).append(
                    DynamicTransferOption(
                        source_route_id=source_route_id,
                        source_line_id=source_route.line_id,
                        target_route_id=target_route_id,
                        target_line_id=target_route.line_id,
                        source_position=best_source_position,
                        target_position=best_target_position,
                        estimated_distance_m=best_straight_distance,
                        estimated_minutes=self._estimated_walk_minutes(best_straight_distance),
                    )
                )

        return dynamic_by_source

    def _materialize_transfer_walks(
        self,
        result_path: list[dict],
        walk_cache: dict[tuple[float, float, float, float], WalkingPathResult | None],
    ) -> list[dict]:
        materialized: list[dict] = []
        for item in result_path:
            if item.get('type') != 'TRANSFER_WALK':
                materialized.append(item)
                continue

            walk_key = (
                round(float(item['walk_origin_lat']), 6),
                round(float(item['walk_origin_lng']), 6),
                round(float(item['walk_destination_lat']), 6),
                round(float(item['walk_destination_lng']), 6),
            )
            if walk_key not in walk_cache:
                walk_cache[walk_key] = self._walk_between(
                    item['walk_origin_lat'],
                    item['walk_origin_lng'],
                    item['walk_destination_lat'],
                    item['walk_destination_lng'],
                    allow_straight_fallback=False,
                )
            walk = walk_cache[walk_key]
            if walk is None:
                materialized.append(item)
                continue

            updated = dict(item)
            updated['distance_m'] = walk.distance_m
            updated['estimated_minutes'] = walk.estimated_minutes
            updated['geometry'] = walk.geometry
            materialized.append(updated)
        return materialized

    def _format_route_response(self, total_cost: float, result_path: list[dict]) -> dict:
        steps: list[dict] = []
        full_geometry: list[dict] = []
        total_walking_distance = 0.0
        transfer_count = 0
        order = 1
        selected_lines: list[str] = []
        walk_segments = 0

        for item in result_path:
            item_type = item['type']
            geometry = item.get('geometry', []) or []
            if geometry:
                if full_geometry and geometry and full_geometry[-1] == geometry[0]:
                    full_geometry.extend(geometry[1:])
                else:
                    full_geometry.extend(geometry)

            if item_type == 'WALK_START':
                walk_segments += 1
                total_walking_distance += float(item['distance_m'])
                steps.append(
                    {
                        'order': order,
                        'type': 'WALK',
                        'title': 'Camina hasta el punto de subida',
                        'description': f"Camina {int(round(item['distance_m']))} metros hasta la línea {item['line_name']}.",
                        'distance_meters': int(round(item['distance_m'])),
                        'estimated_minutes': int(round(item['estimated_minutes'])),
                        'geometry': geometry,
                    }
                )
                order += 1
            elif item_type in {'BUS_TRANSFER', 'BUS_FINAL'}:
                if item['line_name'] not in selected_lines:
                    selected_lines.append(item['line_name'])
                estimated_minutes = int(round(item['estimated_minutes']))
                if estimated_minutes == 0 and float(item['distance_m']) > 0:
                    estimated_minutes = 1
                steps.append(
                    {
                        'order': order,
                        'type': 'BUS',
                        'title': f"Toma la línea {item['line_name']}",
                        'description': 'Recorre este tramo en microbús.',
                        'line_name': item['line_name'],
                        'distance_meters': int(round(item['distance_m'])),
                        'estimated_minutes': estimated_minutes,
                        'geometry': geometry,
                    }
                )
                order += 1
            elif item_type == 'TRANSFER':
                transfer_count += 1
                steps.append(
                    {
                        'order': order,
                        'type': 'TRANSFER',
                        'title': 'Realiza transbordo',
                        'description': f"Penalización de {int(round(item['estimated_minutes']))} minutos en el punto de transbordo.",
                        'distance_meters': 0,
                        'estimated_minutes': int(round(item['estimated_minutes'])),
                        'geometry': geometry,
                    }
                )
                order += 1
            elif item_type == 'TRANSFER_WALK':
                transfer_count += 1
                walk_segments += 1
                total_walking_distance += float(item['distance_m'])
                steps.append(
                    {
                        'order': order,
                        'type': 'WALK',
                        'title': f"Transborda hacia la línea {item['to_line_name']}",
                        'description': f"Camina {int(round(item['distance_m']))} metros para cambiar de línea.",
                        'distance_meters': int(round(item['distance_m'])),
                        'estimated_minutes': int(round(item['estimated_minutes'])),
                        'geometry': geometry,
                    }
                )
                order += 1
            elif item_type == 'WALK_END':
                walk_segments += 1
                total_walking_distance += float(item['distance_m'])
                steps.append(
                    {
                        'order': order,
                        'type': 'WALK',
                        'title': 'Camina hasta tu destino',
                        'description': f"Camina {int(round(item['distance_m']))} metros hasta llegar.",
                        'distance_meters': int(round(item['distance_m'])),
                        'estimated_minutes': int(round(item['estimated_minutes'])),
                        'geometry': geometry,
                    }
                )
                order += 1

        return {
            'total_estimated_minutes': int(round(total_cost)),
            'total_walking_distance_meters': int(round(total_walking_distance)),
            'transfer_count': transfer_count,
            'lines': selected_lines,
            'steps': steps,
            'geometry': full_geometry,
            '_walk_segments': walk_segments,
        }

    def calculate(self, db: Session, *, origin: dict, destination: dict, max_transfers: int, boarding_mode: str):
        max_walk = 1500.0
        walk_cache: dict[tuple[float, float, float, float], WalkingPathResult | None] = {}

        routes, routes_by_line = self._load_routes(db)
        transfers = self._load_transfers(db)
        if not routes:
            return None

        origin_candidates = self._candidate_points(
            routes=routes,
            lat=origin['lat'],
            lng=origin['lng'],
            max_walk_m=max_walk,
            boarding_mode=boarding_mode,
            walk_cache=walk_cache,
        )
        destination_candidates = self._candidate_points(
            routes=routes,
            lat=destination['lat'],
            lng=destination['lng'],
            max_walk_m=max_walk,
            boarding_mode=boarding_mode,
            walk_cache=walk_cache,
        )
        dynamic_transfers = self._build_dynamic_transfers(
            routes=routes,
            max_walk_m=max_walk,
            stop_only=boarding_mode == 'STOPS_ONLY',
        )

        if not any(origin_candidates.values()) and not any(destination_candidates.values()):
            walk_only = self._walk_between(
                origin['lat'],
                origin['lng'],
                destination['lat'],
                destination['lng'],
                allow_straight_fallback=False,
            )
            if walk_only is None:
                return {
                    'total_estimated_minutes': 0,
                    'total_walking_distance_meters': 0,
                    'transfer_count': 0,
                    'lines': [],
                    'steps': [],
                    'geometry': [],
                    'fallback_mode': 'NO_WALKING_PATH',
                    'fallback_message': 'No existe una ruta peatonal OSM valida entre origen y destino.',
                }
            return {
                'total_estimated_minutes': walk_only.estimated_minutes,
                'total_walking_distance_meters': int(round(walk_only.distance_m)),
                'transfer_count': 0,
                'lines': [],
                'steps': [
                    {
                        'order': 1,
                        'type': 'WALK',
                        'title': 'Camina hasta tu destino',
                        'description': 'No se encontró una combinación de líneas; se muestra la mejor caminata peatonal OSM.',
                        'distance_meters': int(round(walk_only.distance_m)),
                        'estimated_minutes': walk_only.estimated_minutes,
                        'geometry': walk_only.geometry,
                    }
                ],
                'geometry': walk_only.geometry,
                'fallback_mode': 'WALK_ONLY',
                'fallback_message': 'No se encontró una ruta de micro con las condiciones seleccionadas.',
                'walking_source': walk_only.source,
            }

        transfer_positions: dict[tuple[int, int], RoutePosition] = {}
        stop_only = boarding_mode == 'STOPS_ONLY'
        for transfer in transfers:
            for line_id in (transfer.source_line_id, transfer.destination_line_id):
                for route_id in routes_by_line.get(line_id, []):
                    key = (route_id, transfer.transfer_id)
                    if key not in transfer_positions:
                        route = routes[route_id]
                        position = route.position_for_point_id(transfer.point_id, stop_only=stop_only)
                        if position is None and not stop_only:
                            position = route.nearest_position(transfer.lat, transfer.lng)
                        if position is not None:
                            transfer_positions[key] = position

        complete_results: list[tuple[float, list[dict], tuple[int, ...]]] = []
        sequence = count()
        pq: list[tuple[float, int, int, int, float, list[dict], tuple[int, ...]]] = []
        best_cost_by_state: dict[tuple[int, int, int], float] = {}

        for route_candidates in origin_candidates.values():
            for candidate in route_candidates:
                heappush(
                    pq,
                    (
                        float(candidate.walk.estimated_minutes),
                        next(sequence),
                        0,
                        candidate.route_id,
                        candidate.position.scalar,
                        [
                            {
                                'type': 'WALK_START',
                                'route_id': candidate.route_id,
                                'line_name': candidate.line_name,
                                'distance_m': candidate.walk.distance_m,
                                'estimated_minutes': candidate.walk.estimated_minutes,
                                'geometry': candidate.walk.geometry,
                            }
                        ],
                        (candidate.line_id,),
                    ),
                )

        while pq:
            cost, _, transfers_used, route_id, scalar_position, path, line_chain = heappop(pq)
            state_key = (route_id, int(round(scalar_position * 1000)), transfers_used)
            if best_cost_by_state.get(state_key, float('inf')) <= cost:
                continue
            best_cost_by_state[state_key] = cost

            route = routes[route_id]
            current_position = route.position_from_scalar(scalar_position)
            for destination_candidate in destination_candidates.get(route_id, []):
                if (
                    not route.is_circular
                    and destination_candidate.position.scalar <= current_position.scalar
                ):
                    continue
                bus_minutes = route.partial_minutes_position(
                    current_position, destination_candidate.position
                )
                bus_distance = route.partial_distance_position(
                    current_position, destination_candidate.position
                )
                bus_geometry = route.geometry_between_positions(
                    current_position, destination_candidate.position
                )
                total_cost = (
                    cost
                    + bus_minutes
                    + destination_candidate.walk.estimated_minutes
                )
                result_path = path + [
                    {
                        'type': 'BUS_FINAL',
                        'route_id': route_id,
                        'line_name': route.line_name,
                        'distance_m': bus_distance,
                        'estimated_minutes': bus_minutes,
                        'geometry': bus_geometry,
                    },
                    {
                        'type': 'WALK_END',
                        'route_id': route_id,
                        'line_name': route.line_name,
                        'distance_m': destination_candidate.walk.distance_m,
                        'estimated_minutes': destination_candidate.walk.estimated_minutes,
                        'geometry': list(reversed(destination_candidate.walk.geometry)),
                    },
                ]
                complete_results.append((total_cost, result_path, line_chain))

            if transfers_used >= max_transfers:
                continue

            for transfer in transfers:
                if transfer.source_line_id != route.line_id:
                    continue
                source_position = transfer_positions.get((route_id, transfer.transfer_id))
                if source_position is None:
                    continue
                if not route.is_circular and source_position.scalar <= current_position.scalar:
                    continue

                bus_to_transfer_minutes = route.partial_minutes_position(current_position, source_position)
                bus_to_transfer_distance = route.partial_distance_position(current_position, source_position)
                bus_to_transfer_geometry = route.geometry_between_positions(current_position, source_position)

                for target_route_id in routes_by_line.get(transfer.destination_line_id, []):
                    target_position = transfer_positions.get((target_route_id, transfer.transfer_id))
                    if target_position is None:
                        continue
                    next_line_chain = line_chain + (routes[target_route_id].line_id,)
                    heappush(
                        pq,
                        (
                            cost + bus_to_transfer_minutes + transfer.penalty_minutes,
                            next(sequence),
                            transfers_used + 1,
                            target_route_id,
                            target_position.scalar,
                            path
                            + [
                                {
                                    'type': 'BUS_TRANSFER',
                                    'route_id': route_id,
                                    'line_name': route.line_name,
                                    'distance_m': bus_to_transfer_distance,
                                    'estimated_minutes': bus_to_transfer_minutes,
                                    'geometry': bus_to_transfer_geometry,
                                },
                                {
                                    'type': 'TRANSFER',
                                    'route_id': target_route_id,
                                    'line_name': routes[target_route_id].line_name,
                                    'distance_m': 0.0,
                                    'estimated_minutes': transfer.penalty_minutes,
                                    'geometry': [{'lat': transfer.lat, 'lng': transfer.lng}],
                                },
                            ],
                            next_line_chain,
                        ),
                    )

            for transfer in dynamic_transfers.get(route_id, []):
                if (
                    not route.is_circular
                    and transfer.source_position.scalar <= current_position.scalar
                ):
                    continue
                if transfer.target_position.scalar >= routes[transfer.target_route_id].last_index and not routes[transfer.target_route_id].is_circular:
                    continue

                bus_to_transfer_minutes = route.partial_minutes_position(current_position, transfer.source_position)
                bus_to_transfer_distance = route.partial_distance_position(current_position, transfer.source_position)
                bus_to_transfer_geometry = route.geometry_between_positions(current_position, transfer.source_position)
                next_line_chain = line_chain + (routes[transfer.target_route_id].line_id,)

                heappush(
                    pq,
                        (
                            cost + bus_to_transfer_minutes + transfer.estimated_minutes,
                            next(sequence),
                            transfers_used + 1,
                            transfer.target_route_id,
                        transfer.target_position.scalar,
                        path
                        + [
                            {
                                'type': 'BUS_TRANSFER',
                                'route_id': route_id,
                                'line_name': route.line_name,
                                'distance_m': bus_to_transfer_distance,
                                'estimated_minutes': bus_to_transfer_minutes,
                                'geometry': bus_to_transfer_geometry,
                            },
                                {
                                    'type': 'TRANSFER_WALK',
                                    'route_id': transfer.target_route_id,
                                    'line_name': routes[transfer.target_route_id].line_name,
                                    'to_line_name': routes[transfer.target_route_id].line_name,
                                    'distance_m': transfer.estimated_distance_m,
                                    'estimated_minutes': transfer.estimated_minutes,
                                    'geometry': [
                                        {'lat': transfer.source_position.lat, 'lng': transfer.source_position.lng},
                                        {'lat': transfer.target_position.lat, 'lng': transfer.target_position.lng},
                                    ],
                                    'walk_origin_lat': transfer.source_position.lat,
                                    'walk_origin_lng': transfer.source_position.lng,
                                    'walk_destination_lat': transfer.target_position.lat,
                                    'walk_destination_lng': transfer.target_position.lng,
                                },
                            ],
                            next_line_chain,
                    ),
                )

        if not complete_results:
            walk_only = self._walk_between(
                origin['lat'],
                origin['lng'],
                destination['lat'],
                destination['lng'],
                allow_straight_fallback=False,
            )
            if walk_only is None:
                return {
                    'total_estimated_minutes': 0,
                    'total_walking_distance_meters': 0,
                    'transfer_count': 0,
                    'lines': [],
                    'steps': [],
                    'geometry': [],
                    'fallback_mode': 'NO_WALKING_PATH',
                    'fallback_message': 'No se encontró una ruta peatonal OSM ni una combinación válida de líneas.',
                }
            return {
                'total_estimated_minutes': walk_only.estimated_minutes,
                'total_walking_distance_meters': int(round(walk_only.distance_m)),
                'transfer_count': 0,
                'lines': [],
                'steps': [
                    {
                        'order': 1,
                        'type': 'WALK',
                        'title': 'Camina hasta tu destino',
                        'description': 'No se encontró una ruta de micro válida; se muestra caminata peatonal OSM.',
                        'distance_meters': int(round(walk_only.distance_m)),
                        'estimated_minutes': walk_only.estimated_minutes,
                        'geometry': walk_only.geometry,
                    }
                ],
                'geometry': walk_only.geometry,
                'fallback_mode': 'WALK_ONLY',
                'fallback_message': 'No se encontró una ruta de micro con las condiciones seleccionadas.',
                'walking_source': walk_only.source,
                'routes': [
                    {
                        'total_estimated_minutes': walk_only.estimated_minutes,
                        'total_walking_distance_meters': int(round(walk_only.distance_m)),
                        'transfer_count': 0,
                        'lines': [],
                        'steps': [
                            {
                                'order': 1,
                                'type': 'WALK',
                                'title': 'Camina hasta tu destino',
                                'description': 'No se encontró una ruta de micro válida; se muestra caminata peatonal OSM.',
                                'distance_meters': int(round(walk_only.distance_m)),
                                'estimated_minutes': walk_only.estimated_minutes,
                                'geometry': walk_only.geometry,
                            }
                        ],
                        'geometry': walk_only.geometry,
                    }
                ],
                'route_count': 1,
                'selected_route_index': 0,
            }

        unique_signatures: set[tuple] = set()
        provisional_routes: list[tuple[dict, list[dict]]] = []
        for total_cost, result_path, _line_chain in complete_results:
            route_response = self._format_route_response(total_cost, result_path)
            signature = (
                tuple(route_response['lines']),
                route_response['transfer_count'],
                route_response['total_walking_distance_meters'],
                route_response['total_estimated_minutes'],
            )
            if signature in unique_signatures:
                continue
            unique_signatures.add(signature)
            provisional_routes.append((route_response, result_path))

        provisional_routes.sort(
            key=lambda route_item: (
                route_item[0]['total_estimated_minutes'],
                route_item[0]['transfer_count'],
                route_item[0]['total_walking_distance_meters'],
                route_item[0]['_walk_segments'],
            )
        )
        provisional_routes = provisional_routes[: self.max_route_results]

        routes_response: list[dict] = []
        for route_response, result_path in provisional_routes:
            materialized_path = self._materialize_transfer_walks(result_path, walk_cache)
            exact_total_cost = sum(float(item.get('estimated_minutes', 0)) for item in materialized_path)
            exact_response = self._format_route_response(exact_total_cost, materialized_path)
            routes_response.append(exact_response)

        routes_response.sort(
            key=lambda route: (
                route['total_estimated_minutes'],
                route['transfer_count'],
                route['total_walking_distance_meters'],
                route['_walk_segments'],
            )
        )
        primary_route = routes_response[0]
        for route in routes_response:
            route.pop('_walk_segments', None)
        return {
            **primary_route,
            'routes': routes_response,
            'primary_route': primary_route,
            'route_count': len(routes_response),
            'selected_route_index': 0,
            'selection_basis': 'fastest_time_then_transfers_then_walking',
        }
