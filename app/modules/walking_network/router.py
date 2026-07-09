from fastapi import APIRouter, HTTPException

from app.modules.walking_network.schemas import WalkingRouteRequest
from app.modules.walking_network.service import WalkingNetworkService
from app.shared.responses.helpers import ok

router = APIRouter(prefix='/walking-network', tags=['walking_network'])
service = WalkingNetworkService()


@router.get('/health')
def walking_network_health():
    return ok(data={'status': 'ready'}, message='Walking network disponible')


@router.post('/route')
def walking_route(payload: WalkingRouteRequest):
    result = service.route(
        origin_lat=payload.origin_lat,
        origin_lng=payload.origin_lng,
        destination_lat=payload.destination_lat,
        destination_lng=payload.destination_lng,
        allow_straight_fallback=True,
    )
    if result is None:
        raise HTTPException(
            status_code=503,
            detail='Red peatonal OSM no disponible o sin camino entre los puntos solicitados.',
        )
    return ok(
        data={
            'distance_m': round(result.distance_m, 2),
            'estimated_minutes': result.estimated_minutes,
            'geometry': result.geometry,
            'source': result.source,
        },
        message='Ruta peatonal calculada correctamente',
    )
