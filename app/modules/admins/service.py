from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import AppException
from app.core.security import get_password_hash
from app.modules.admins.models import Admin
from app.modules.admins.schemas import AdminCreateRequest, AdminUpdateRequest


class AdminsService:
    def list_admins(self, db: Session) -> list[Admin]:
        return db.scalars(select(Admin).order_by(Admin.created_at.desc())).all()

    def get_admin(self, db: Session, admin_id: str) -> Admin:
        admin = db.get(Admin, admin_id)
        if not admin:
            raise AppException(message='Administrador no encontrado', error_code='ADMIN_NOT_FOUND', status_code=404)
        return admin

    def create_admin(self, db: Session, payload: AdminCreateRequest) -> Admin:
        exists = db.scalar(select(Admin).where(func.lower(Admin.email) == payload.email.lower()))
        if exists:
            raise AppException(message='Email ya registrado', error_code='EMAIL_ALREADY_EXISTS', status_code=409)

        role = payload.role.upper()
        if role not in {'ADMIN', 'SUPER_ADMIN'}:
            raise AppException(message='Rol invalido', error_code='INVALID_ROLE', status_code=422)

        admin = Admin(
            email=payload.email.lower(),
            password_hash=get_password_hash(payload.password),
            full_name=payload.full_name,
            role=role,
            is_active=True,
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
        return admin

    def update_admin(self, db: Session, admin_id: str, payload: AdminUpdateRequest) -> Admin:
        admin = self.get_admin(db, admin_id)

        if payload.role is not None:
            next_role = payload.role.upper()
            if next_role not in {'ADMIN', 'SUPER_ADMIN'}:
                raise AppException(message='Rol invalido', error_code='INVALID_ROLE', status_code=422)
            admin.role = next_role

        if payload.full_name is not None:
            admin.full_name = payload.full_name

        if payload.is_active is not None:
            if admin.role == 'SUPER_ADMIN' and payload.is_active is False:
                active_super_admins = db.scalar(
                    select(func.count()).select_from(Admin).where(Admin.role == 'SUPER_ADMIN', Admin.is_active.is_(True))
                )
                if (active_super_admins or 0) <= 1:
                    raise AppException(
                        message='No se puede desactivar el ultimo SUPER_ADMIN',
                        error_code='LAST_SUPER_ADMIN_PROTECTED',
                        status_code=409,
                    )
            admin.is_active = payload.is_active

        db.add(admin)
        db.commit()
        db.refresh(admin)
        return admin
