from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.modules.nearby_lines.schemas import NearbyLinesSearchRequest
from app.modules.nearby_lines.service import NearbyLinesService
from app.shared.responses.helpers import ok

router = APIRouter(prefix='/nearby-lines', tags=['nearby_lines'])
service = NearbyLinesService()


@router.post('/search')
def search_nearby_lines(payload: NearbyLinesSearchRequest, db: Session = Depends(get_db)):
    lines = service.search(db, lat=payload.lat, lng=payload.lng, radius_m=payload.radius_m)
    if not lines:
        return ok(data=[], message='No se encontraron líneas cercanas.')
    return ok(data=lines)
