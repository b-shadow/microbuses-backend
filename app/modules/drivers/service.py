from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import AppException
from app.core.security import get_password_hash
from app.modules.audit.models import AuditLog
from app.modules.drivers.models import Driver
from app.modules.drivers.schemas import DriverCreateRequest, DriverDecisionRequest, DriverUpdateRequest


class DriversService:
    def _audit(self, db: Session, *, actor, action: str, entity_id: str, detail: dict | None = None) -> None:
        log = AuditLog(
            actor_id=getattr(actor, 'id', None),
            actor_type=actor.__class__.__name__.upper() if actor else 'SYSTEM',
            action=action,
            entity='drivers',
            entity_id=entity_id,
            detail=detail or {},
            created_at=datetime.now(),
        )
        db.add(log)

    def list_drivers(self, db: Session, approval_status: str | None = None) -> list[Driver]:
        query = select(Driver).order_by(Driver.created_at.desc())
        if approval_status:
            query = query.where(Driver.approval_status == approval_status)
        return db.scalars(query).all()

    def get_driver(self, db: Session, driver_id: str) -> Driver:
        driver = db.get(Driver, driver_id)
        if not driver:
            raise AppException(message='Conductor no encontrado', error_code='DRIVER_NOT_FOUND', status_code=404)
        return driver

    def create_driver(self, db: Session, payload: DriverCreateRequest) -> Driver:
        exists_email = db.scalar(select(Driver).where(func.lower(Driver.email) == payload.email.lower()))
        if exists_email:
            raise AppException(message='Email ya registrado', error_code='EMAIL_ALREADY_EXISTS', status_code=409)

        exists_ci = db.scalar(select(Driver).where(Driver.ci == payload.ci))
        if exists_ci:
            raise AppException(message='CI ya registrado', error_code='CI_ALREADY_EXISTS', status_code=409)

        driver = Driver(
            email=payload.email.lower(),
            password_hash=get_password_hash(payload.password),
            ci=payload.ci,
            full_name=payload.full_name,
            birth_date=payload.birth_date,
            sex=payload.sex,
            phone=payload.phone,
            license_category=payload.license_category,
            photo_url=payload.photo_url,
            approval_status='PENDING',
            is_active=True,
        )
        db.add(driver)
        db.commit()
        db.refresh(driver)
        return driver

    def update_driver(self, db: Session, driver_id: str, payload: DriverUpdateRequest, actor) -> Driver:
        driver = self.get_driver(db, driver_id)
        old_data = {
            'full_name': driver.full_name,
            'phone': driver.phone,
            'license_category': driver.license_category,
            'is_active': driver.is_active,
        }

        data = payload.model_dump(exclude_none=True)
        for key, value in data.items():
            setattr(driver, key, value)

        db.add(driver)
        self._audit(
            db,
            actor=actor,
            action='DRIVER_UPDATED',
            entity_id=str(driver.id),
            detail={'old_value': old_data, 'new_value': data},
        )
        db.commit()
        db.refresh(driver)
        return driver

    def set_status(self, db: Session, driver_id: str, status: str, actor, decision: DriverDecisionRequest | None = None) -> Driver:
        driver = self.get_driver(db, driver_id)
        previous = driver.approval_status
        driver.approval_status = status
        db.add(driver)

        action = 'DRIVER_APPROVED' if status == 'APPROVED' else 'DRIVER_REJECTED'
        self._audit(
            db,
            actor=actor,
            action=action,
            entity_id=str(driver.id),
            detail={
                'old_value': {'approval_status': previous},
                'new_value': {'approval_status': status},
                'reason': decision.reason if decision else None,
            },
        )
        db.commit()
        db.refresh(driver)
        return driver

    def delete_driver(self, db: Session, driver_id: str, actor) -> None:
        driver = self.get_driver(db, driver_id)
        self._audit(
            db,
            actor=actor,
            action='DRIVER_DELETED',
            entity_id=str(driver.id),
            detail={
                'email': driver.email,
                'full_name': driver.full_name,
                'ci': driver.ci,
            },
        )
        db.delete(driver)
        db.commit()
