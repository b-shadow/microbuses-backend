from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import AppException
from app.core.security import create_access_token, get_password_hash, verify_password
from app.modules.auth.repository import AuthRepository
from app.modules.auth.schemas import LoginRequest, RegisterDriverRequest, RegisterUserRequest
from app.modules.drivers.models import Driver
from app.modules.users.models import User


class AuthService:
    def __init__(self) -> None:
        self.repository = AuthRepository()

    def login(self, db: Session, payload: LoginRequest):
        found = self.repository.find_by_email(db, payload.email)
        if not found:
            raise AppException(message='Credenciales inválidas', error_code='INVALID_CREDENTIALS', status_code=401)

        role, actor = found
        if not verify_password(payload.password, actor.password_hash):
            raise AppException(message='Credenciales inválidas', error_code='INVALID_CREDENTIALS', status_code=401)

        if hasattr(actor, 'is_active') and not actor.is_active:
            raise AppException(message='Cuenta inactiva', error_code='ACCOUNT_INACTIVE', status_code=403)

        if role == 'DRIVER' and getattr(actor, 'approval_status', None) != 'APPROVED':
            raise AppException(message='Conductor no aprobado', error_code='DRIVER_NOT_APPROVED', status_code=403)

        return {
            'access_token': create_access_token(subject=str(actor.id), role=role),
            'role': role,
        }

    def register_user(self, db: Session, payload: RegisterUserRequest):
        if self.repository.find_by_email(db, payload.email):
            raise AppException(message='Email ya registrado', error_code='EMAIL_ALREADY_EXISTS', status_code=409)

        user = User(
            email=payload.email,
            password_hash=get_password_hash(payload.password),
            names=payload.names,
            last_names=payload.last_names,
            phone=payload.phone,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    def register_driver(self, db: Session, payload: RegisterDriverRequest):
        if self.repository.find_by_email(db, payload.email):
            raise AppException(message='Email ya registrado', error_code='EMAIL_ALREADY_EXISTS', status_code=409)

        exists_ci = db.scalar(select(Driver).where(Driver.ci == payload.ci))
        if exists_ci:
            raise AppException(message='CI ya registrado', error_code='CI_ALREADY_EXISTS', status_code=409)

        driver = Driver(
            email=payload.email,
            password_hash=get_password_hash(payload.password),
            ci=payload.ci,
            full_name=payload.full_name,
            phone=payload.phone,
            license_category=payload.license_category,
            approval_status='PENDING',
        )
        db.add(driver)
        db.commit()
        db.refresh(driver)
        return driver
