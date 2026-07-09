from __future__ import annotations

from dataclasses import dataclass
from math import atan2, cos, radians, sin, sqrt
from pathlib import Path
import pickle
from typing import Any

from app.core.settings import get_settings


@dataclass
class WalkingPathResult:
    distance_m: float
    estimated_minutes: int
    geometry: list[dict]
    source: str


class WalkingNetworkService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self._graph: Any | None = None
        self._nx: Any | None = None
        self._ox: Any | None = None

    def _load_libs(self) -> bool:
        if self._nx is not None and self._ox is not None:
            return True
        try:
            import networkx as nx  # type: ignore
            import osmnx as ox  # type: ignore
        except Exception:
            return False
        self._nx = nx
        self._ox = ox
        return True

    def _load_graph(self) -> Any | None:
        if not self._load_libs():
            return None
        if self._graph is not None:
            return self._graph

        path = Path(self.settings.walking_graph_path)
        pickle_path = path.with_suffix('.pkl')
        if pickle_path.exists():
            with pickle_path.open('rb') as fh:
                self._graph = pickle.load(fh)
            return self._graph

        if not path.exists():
            return None

        self._graph = self._ox.load_graphml(path)
        return self._graph

    def preload_graph(self) -> bool:
        return self._load_graph() is not None

    def _walking_minutes(self, distance_m: float) -> int:
        speed = self.settings.walking_default_speed_kmh
        minutes = distance_m / (speed * 1000 / 60)
        return max(1, int(round(minutes)))

    def _haversine_m(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        r = 6371000.0
        dlat = radians(lat2 - lat1)
        dlng = radians(lng2 - lng1)
        a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlng / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        return r * c

    def _fallback_straight(self, origin_lat: float, origin_lng: float, destination_lat: float, destination_lng: float) -> WalkingPathResult:
        distance_m = self._haversine_m(origin_lat, origin_lng, destination_lat, destination_lng)
        return WalkingPathResult(
            distance_m=distance_m,
            estimated_minutes=self._walking_minutes(distance_m),
            geometry=[
                {'lat': origin_lat, 'lng': origin_lng},
                {'lat': destination_lat, 'lng': destination_lng},
            ],
            source='fallback_straight',
        )

    def route(
        self,
        *,
        origin_lat: float,
        origin_lng: float,
        destination_lat: float,
        destination_lng: float,
        allow_straight_fallback: bool = False,
    ) -> WalkingPathResult | None:
        graph = self._load_graph()
        if graph is None:
            if allow_straight_fallback:
                return self._fallback_straight(origin_lat, origin_lng, destination_lat, destination_lng)
            return None

        try:
            origin_node = self._ox.distance.nearest_nodes(graph, X=origin_lng, Y=origin_lat)
            destination_node = self._ox.distance.nearest_nodes(graph, X=destination_lng, Y=destination_lat)
            node_path = self._nx.shortest_path(graph, origin_node, destination_node, weight='length')

            # For very short movements both coordinates can snap to the same node.
            # In that case there is still a valid pedestrian segment between the
            # requested coordinates even though the graph path has a single node.
            if len(node_path) < 2:
                return WalkingPathResult(
                    distance_m=self._haversine_m(origin_lat, origin_lng, destination_lat, destination_lng),
                    estimated_minutes=self._walking_minutes(
                        self._haversine_m(origin_lat, origin_lng, destination_lat, destination_lng)
                    ),
                    geometry=[
                        {'lat': origin_lat, 'lng': origin_lng},
                        {'lat': destination_lat, 'lng': destination_lng},
                    ],
                    source='osm_same_node',
                )

            distance_m = 0.0
            geometry = []

            for idx in range(len(node_path) - 1):
                u = node_path[idx]
                v = node_path[idx + 1]
                edge_data = graph.get_edge_data(u, v)
                if not edge_data:
                    continue
                edge = min(edge_data.values(), key=lambda x: float(x.get('length', 0.0)))
                distance_m += float(edge.get('length', 0.0))

            for n in node_path:
                data = graph.nodes[n]
                geometry.append({'lat': float(data['y']), 'lng': float(data['x'])})
            return WalkingPathResult(
                distance_m=distance_m,
                estimated_minutes=self._walking_minutes(distance_m),
                geometry=geometry,
                source='osm_graph',
            )
        except Exception:
            if allow_straight_fallback:
                return self._fallback_straight(origin_lat, origin_lng, destination_lat, destination_lng)
            return None
