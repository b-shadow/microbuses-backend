from app.modules.routing_engine.service import (
    DynamicTransferOption,
    TransferOption,
    RouteData,
    RoutePoint,
    RoutePosition,
    RoutingEngineService,
    WalkingPathResult,
    haversine_m,
)


def _make_walk(lat1: float, lng1: float, lat2: float, lng2: float) -> WalkingPathResult:
    distance = haversine_m(lat1, lng1, lat2, lng2)
    estimated = max(1, int(round(distance / 75)))
    return WalkingPathResult(
        distance_m=distance,
        estimated_minutes=estimated,
        geometry=[
            {'lat': lat1, 'lng': lng1},
            {'lat': lat2, 'lng': lng2},
        ],
        source='test',
    )


def _make_route(
    route_id: int,
    line_id: int,
    line_name: str,
    coords: list[tuple[float, float]],
    *,
    segment_minutes: float = 2.0,
    stops: set[int] | None = None,
    point_ids: list[int] | None = None,
) -> RouteData:
    stops = stops or set()
    points = [
        RoutePoint(
            lat=lat,
            lng=lng,
            point_id=point_ids[index] if point_ids is not None else None,
            stop='S' if index in stops else 'N',
        )
        for index, (lat, lng) in enumerate(coords)
    ]
    segment_count = len(points) - 1
    return RouteData(
        route_id=route_id,
        line_id=line_id,
        line_name=line_name,
        line_color='#FF0000',
        points=points,
        segment_distances=[100.0] * segment_count,
        segment_minutes=[segment_minutes] * segment_count,
    )


def test_route_data_wraps_on_circular_routes():
    route = _make_route(
        1,
        101,
        'L001',
        [
            (0.0, 0.0),
            (0.0, 0.001),
            (0.001, 0.001),
            (0.001, 0.0),
            (0.0, 0.0),
        ],
    )
    start = RoutePosition(
        segment_index=3,
        offset=0.5,
        lat=0.0005,
        lng=0.0,
        straight_distance_m=0.0,
    )
    end = RoutePosition(
        segment_index=1,
        offset=0.5,
        lat=0.0005,
        lng=0.001,
        straight_distance_m=0.0,
    )

    assert route.is_circular is True
    assert route.partial_minutes_position(start, end) == 4.0
    assert route.partial_distance_position(start, end) == 200.0
    geometry = route.geometry_between_positions(start, end)
    assert len(geometry) >= 4
    assert geometry[0] == {'lat': start.lat, 'lng': start.lng}
    assert geometry[-1] == {'lat': end.lat, 'lng': end.lng}


def test_calculate_supports_walk_bus_transfer_bus_paths(monkeypatch):
    service = RoutingEngineService()

    route_1 = _make_route(
        1,
        101,
        'L001',
        [(0.0, 0.0), (0.0, 0.01), (0.0, 0.02)],
        segment_minutes=2.0,
    )
    route_2 = _make_route(
        2,
        102,
        'L002',
        [(0.0, 0.0208), (0.0, 0.028), (0.0, 0.0354)],
        segment_minutes=2.0,
    )
    routes = {1: route_1, 2: route_2}
    routes_by_line = {101: [1], 102: [2]}

    monkeypatch.setattr(service, '_load_routes', lambda db: (routes, routes_by_line))
    monkeypatch.setattr(service, '_load_transfers', lambda db: [])
    monkeypatch.setattr(
        service,
        '_walk_between',
        lambda from_lat, from_lng, to_lat, to_lng, allow_straight_fallback=False: _make_walk(
            from_lat, from_lng, to_lat, to_lng
        ),
    )

    transfer_walk = _make_walk(0.0, 0.02, 0.0, 0.0208)
    transfer = DynamicTransferOption(
        source_route_id=1,
        source_line_id=101,
        target_route_id=2,
        target_line_id=102,
        source_position=RoutePosition(
            segment_index=1,
            offset=1.0,
            lat=0.0,
            lng=0.02,
            straight_distance_m=0.0,
        ),
        target_position=RoutePosition(
            segment_index=0,
            offset=0.0,
            lat=0.0,
            lng=0.0208,
            straight_distance_m=0.0,
        ),
        estimated_distance_m=transfer_walk.distance_m,
        estimated_minutes=transfer_walk.estimated_minutes,
    )
    monkeypatch.setattr(service, '_build_dynamic_transfers', lambda **kwargs: {1: [transfer]})

    result = service.calculate(
        db=None,
        origin={'lat': 0.0, 'lng': 0.00005},
        destination={'lat': 0.0, 'lng': 0.03545},
        max_transfers=3,
        boarding_mode='ANYWHERE_ON_ROUTE',
    )

    assert result is not None
    assert result['route_count'] >= 1
    assert result.get('fallback_mode') is None
    assert result['lines'] == ['L001', 'L002']
    step_types = [step['type'] for step in result['steps']]
    assert 'BUS' in step_types
    assert result['transfer_count'] >= 1


def test_calculate_limits_route_results_to_eight(monkeypatch):
    service = RoutingEngineService()

    routes: dict[int, RouteData] = {}
    routes_by_line: dict[int, list[int]] = {}
    base_lat = -17.7800
    for index in range(10):
        route_id = index + 1
        line_id = 100 + route_id
        lat = base_lat + (index * 0.00001)
        route = _make_route(
            route_id,
            line_id,
            f'L{route_id:03d}',
            [(lat, -63.2000), (lat, -63.1990), (lat, -63.1980)],
            segment_minutes=2.0 + index,
        )
        routes[route_id] = route
        routes_by_line[line_id] = [route_id]

    monkeypatch.setattr(service, '_load_routes', lambda db: (routes, routes_by_line))
    monkeypatch.setattr(service, '_load_transfers', lambda db: [])
    monkeypatch.setattr(service, '_build_dynamic_transfers', lambda **kwargs: {})
    monkeypatch.setattr(
        service,
        '_walk_between',
        lambda from_lat, from_lng, to_lat, to_lng, allow_straight_fallback=False: _make_walk(
            from_lat, from_lng, to_lat, to_lng
        ),
    )

    result = service.calculate(
        db=None,
        origin={'lat': base_lat, 'lng': -63.20001},
        destination={'lat': base_lat, 'lng': -63.19799},
        max_transfers=0,
        boarding_mode='ANYWHERE_ON_ROUTE',
    )

    assert result is not None
    assert result['route_count'] == 8
    assert len(result['routes']) == 8
    times = [route['total_estimated_minutes'] for route in result['routes']]
    assert times == sorted(times)


def test_calculate_stops_only_uses_stop_transfer_points(monkeypatch):
    service = RoutingEngineService()

    route_1 = _make_route(
        1,
        101,
        'L001',
        [(0.0, 0.0), (0.0, 0.01), (0.0, 0.02)],
        segment_minutes=2.0,
        stops={0, 2},
        point_ids=[1, 2, 3],
    )
    route_2 = _make_route(
        2,
        102,
        'L002',
        [(0.0, 0.02), (0.0, 0.028), (0.0, 0.0354)],
        segment_minutes=2.0,
        stops={0, 2},
        point_ids=[3, 5, 6],
    )
    routes = {1: route_1, 2: route_2}
    routes_by_line = {101: [1], 102: [2]}

    monkeypatch.setattr(service, '_load_routes', lambda db: (routes, routes_by_line))
    monkeypatch.setattr(
        service,
        '_load_transfers',
        lambda db: [
            TransferOption(
                transfer_id=1,
                point_id=3,
                source_line_id=101,
                destination_line_id=102,
                penalty_minutes=1.0,
                lat=0.0,
                lng=0.02,
            )
        ],
    )
    monkeypatch.setattr(
        service,
        '_build_dynamic_transfers',
        lambda **kwargs: {},
    )
    monkeypatch.setattr(
        service,
        '_walk_between',
        lambda from_lat, from_lng, to_lat, to_lng, allow_straight_fallback=False: _make_walk(
            from_lat, from_lng, to_lat, to_lng
        ),
    )

    result = service.calculate(
        db=None,
        origin={'lat': 0.0, 'lng': 0.00005},
        destination={'lat': 0.0, 'lng': 0.03545},
        max_transfers=3,
        boarding_mode='STOPS_ONLY',
    )

    assert result is not None
    assert result['route_count'] >= 1
    assert result.get('fallback_mode') is None
    assert result['lines'] == ['L001', 'L002']
    assert result['transfer_count'] >= 1


def test_build_dynamic_transfers_stops_only_uses_only_stop_points():
    service = RoutingEngineService()
    service.dynamic_transfer_point_stride = 1

    route_1 = _make_route(
        1,
        101,
        'L001',
        [(0.0, 0.0), (0.0, 0.004), (0.0, 0.008)],
        stops={1},
        point_ids=[1, 2, 3],
    )
    route_2 = _make_route(
        2,
        102,
        'L002',
        [(0.0, 0.0041), (0.0, 0.012), (0.0, 0.02)],
        stops={0},
        point_ids=[4, 5, 6],
    )

    transfers = service._build_dynamic_transfers(
        routes={1: route_1, 2: route_2},
        max_walk_m=1000.0,
        stop_only=True,
    )

    assert 1 in transfers
    assert len(transfers[1]) >= 1
    transfer = transfers[1][0]
    assert abs(transfer.source_position.lng - 0.004) < 1e-9
    assert abs(transfer.target_position.lng - 0.0041) < 1e-9
