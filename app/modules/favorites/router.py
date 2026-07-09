from fastapi import APIRouter, Depends
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_actor, get_db
from app.core.exceptions import AppException
from app.core.permissions import require_roles
from app.modules.favorites.models import FavoritePlace
from app.modules.favorites.schemas import FavoriteCreateRequest, FavoritePatchRequest
from app.shared.responses.helpers import ok

router = APIRouter(prefix='/favorites', tags=['favorites'])


@router.get('')
def list_favorites(actor=Depends(get_current_actor), db: Session = Depends(get_db)):
    require_roles(actor, {'USER'})
    rows = db.execute(
        text(
            """
            SELECT
                id::text AS id,
                name,
                ST_Y(location::geometry) AS lat,
                ST_X(location::geometry) AS lng
            FROM favorite_places
            WHERE user_id = :user_id
            ORDER BY created_at DESC
            """
        ),
        {'user_id': str(actor.id)},
    ).mappings().all()
    return ok(data=[dict(r) for r in rows])


@router.post('')
def create_favorite(payload: FavoriteCreateRequest, actor=Depends(get_current_actor), db: Session = Depends(get_db)):
    require_roles(actor, {'USER'})
    row = FavoritePlace(user_id=actor.id, name=payload.name, location=f'SRID=4326;POINT({payload.lng} {payload.lat})')
    db.add(row)
    db.commit()
    db.refresh(row)
    return ok(data={'id': str(row.id), 'name': row.name, 'lat': payload.lat, 'lng': payload.lng}, message='Favorito creado')


@router.patch('/{favorite_id}')
def patch_favorite(favorite_id: str, payload: FavoritePatchRequest, actor=Depends(get_current_actor), db: Session = Depends(get_db)):
    require_roles(actor, {'USER'})
    row = db.get(FavoritePlace, favorite_id)
    if not row or str(row.user_id) != str(actor.id):
        raise AppException(message='Favorito no encontrado', error_code='FAVORITE_NOT_FOUND', status_code=404)

    data = payload.model_dump(exclude_unset=True)
    if 'name' in data:
        row.name = data['name']
    if 'lat' in data or 'lng' in data:
        lat = data.get('lat')
        lng = data.get('lng')
        if lat is None or lng is None:
            raise AppException(message='lat y lng son requeridos juntos', error_code='INVALID_COORDINATES', status_code=400)
        row.location = f'SRID=4326;POINT({lng} {lat})'

    db.add(row)
    db.commit()
    return ok(message='Favorito actualizado')


@router.delete('/{favorite_id}')
def delete_favorite(favorite_id: str, actor=Depends(get_current_actor), db: Session = Depends(get_db)):
    require_roles(actor, {'USER'})
    row = db.get(FavoritePlace, favorite_id)
    if not row or str(row.user_id) != str(actor.id):
        raise AppException(message='Favorito no encontrado', error_code='FAVORITE_NOT_FOUND', status_code=404)
    db.delete(row)
    db.commit()
    return ok(message='Favorito eliminado')