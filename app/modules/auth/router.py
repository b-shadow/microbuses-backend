from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_actor, get_db
from app.core.permissions import resolve_role
from app.modules.auth.schemas import LoginRequest, RegisterDriverRequest, RegisterUserRequest
from app.modules.auth.service import AuthService
from app.shared.responses.helpers import ok

router = APIRouter(prefix='/auth', tags=['auth'])
service = AuthService()


@router.post('/login')
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    token = service.login(db, payload)
    return ok(data=token)


@router.post('/register-user')
def register_user(payload: RegisterUserRequest, db: Session = Depends(get_db)):
    user = service.register_user(db, payload)
    return ok(data={'id': str(user.id), 'email': user.email}, message='Usuario registrado correctamente')


@router.post('/register-driver')
def register_driver(payload: RegisterDriverRequest, db: Session = Depends(get_db)):
    driver = service.register_driver(db, payload)
    return ok(data={'id': str(driver.id), 'email': driver.email, 'status': driver.approval_status}, message='Conductor registrado correctamente')


@router.get('/me')
def me(actor=Depends(get_current_actor)):
    if not actor:
        return ok(data={}, message='No autenticado')

    role = resolve_role(actor)
    data = {
        'id': str(actor.id),
        'email': actor.email,
        'role': role,
    }

    if role == 'DRIVER':
        data['approval_status'] = getattr(actor, 'approval_status', None)
    if role in {'ADMIN', 'SUPER_ADMIN'}:
        data['admin_role'] = getattr(actor, 'role', None)

    return ok(data=data)


@router.post('/logout')
def logout():
    return ok(message='Sesión cerrada correctamente')


@router.post('/refresh')
def refresh():
    return ok(message='Refresh pendiente de implementación')
