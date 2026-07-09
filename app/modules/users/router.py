import re

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_actor, get_db
from app.core.exceptions import AppException
from app.core.security import get_password_hash, verify_password
from app.modules.users.models import User
from app.modules.users.schemas import UserChangePasswordRequest, UserUpdateRequest
from app.shared.responses.helpers import ok

router = APIRouter(prefix='/users', tags=['users'])


_PASSWORD_POLICY = re.compile(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z\d]).{8,}$')


def _user_payload(actor: User) -> dict:
    return {
        'id': str(actor.id),
        'email': actor.email,
        'names': actor.names,
        'last_names': actor.last_names,
        'phone': actor.phone,
        'photo_url': actor.photo_url,
        'is_active': actor.is_active,
    }


@router.get('/me')
def get_me(actor=Depends(get_current_actor)):
    if not isinstance(actor, User):
        return ok(data={}, message='No autorizado')
    return ok(data=_user_payload(actor))


@router.patch('/me')
def patch_me(payload: UserUpdateRequest, actor=Depends(get_current_actor), db: Session = Depends(get_db)):
    if not isinstance(actor, User):
        return ok(data={}, message='No autorizado')
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(actor, key, value)
    db.add(actor)
    db.commit()
    db.refresh(actor)
    return ok(data=_user_payload(actor), message='Perfil actualizado correctamente')


@router.patch('/me/password')
def change_my_password(payload: UserChangePasswordRequest, actor=Depends(get_current_actor), db: Session = Depends(get_db)):
    if not isinstance(actor, User):
        return ok(data={}, message='No autorizado')

    if not verify_password(payload.current_password, actor.password_hash):
        raise AppException(message='La contrasena actual es incorrecta.', error_code='CURRENT_PASSWORD_INVALID', status_code=400)

    if payload.new_password != payload.confirm_password:
        raise AppException(message='La confirmacion no coincide con la nueva contrasena.', error_code='PASSWORD_CONFIRMATION_MISMATCH', status_code=400)

    if not _PASSWORD_POLICY.match(payload.new_password):
        raise AppException(
            message='La nueva contrasena no cumple la politica minima.',
            error_code='PASSWORD_POLICY_FAILED',
            status_code=400,
            details={
                'rules': [
                    'Minimo 8 caracteres',
                    'Al menos 1 mayuscula',
                    'Al menos 1 minuscula',
                    'Al menos 1 numero',
                    'Al menos 1 simbolo',
                ]
            },
        )

    actor.password_hash = get_password_hash(payload.new_password)
    db.add(actor)
    db.commit()

    return ok(message='Contrasena actualizada correctamente')


@router.delete('/me')
def delete_me(actor=Depends(get_current_actor), db: Session = Depends(get_db)):
    if not isinstance(actor, User):
        return ok(data={}, message='No autorizado')
    actor.is_active = False
    db.add(actor)
    db.commit()
    return ok(message='Usuario desactivado correctamente')