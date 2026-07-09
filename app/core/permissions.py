from app.core.exceptions import AppException


ROLE_USER = 'USER'
ROLE_DRIVER = 'DRIVER'
ROLE_ADMIN = 'ADMIN'
ROLE_SUPER_ADMIN = 'SUPER_ADMIN'


def resolve_role(actor) -> str | None:
    role = getattr(actor, 'role', None)
    if actor.__class__.__name__ == 'User':
        return ROLE_USER
    if actor.__class__.__name__ == 'Driver':
        return ROLE_DRIVER
    return role


def require_roles(actor, allowed_roles: set[str]) -> None:
    if not actor:
        raise AppException(message='No autenticado', error_code='UNAUTHENTICATED', status_code=401)

    role = resolve_role(actor)
    if role not in allowed_roles:
        raise AppException(message='No autorizado', error_code='FORBIDDEN', status_code=403)
