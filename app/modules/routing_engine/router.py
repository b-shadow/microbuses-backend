from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.modules.routing_engine.schemas import RoutingRequest
from app.modules.routing_engine.service import RoutingEngineService
from app.shared.responses.helpers import ok

router = APIRouter(prefix='/routing', tags=['routing_engine'])
service = RoutingEngineService()


@router.post('/calculate')
def calculate_route(payload: RoutingRequest, db: Session = Depends(get_db)):
    result = service.calculate(
        db,
        origin=payload.origin.model_dump(),
        destination=payload.destination.model_dump(),
        max_transfers=payload.max_transfers,
        boarding_mode=payload.boarding_mode,
    )
    if not result:
        return ok(
            data={},
            message='No se encontró una ruta disponible con las condiciones seleccionadas.',
        )
    return ok(data=result, message='Ruta calculada correctamente.')
