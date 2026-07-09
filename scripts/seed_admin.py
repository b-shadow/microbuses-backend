import os

from sqlalchemy import select

from app.core.dependencies import SessionLocal
from app.core.security import get_password_hash
from app.core.settings import get_settings
from app.modules.admins.models import Admin


def main() -> None:
    settings = get_settings()
    email = os.getenv('SUPER_ADMIN_EMAIL', settings.super_admin_email)
    password = os.getenv('SUPER_ADMIN_PASSWORD', settings.super_admin_password)
    full_name = os.getenv('SUPER_ADMIN_FULL_NAME', settings.super_admin_full_name)

    with SessionLocal() as db:
        existing = db.scalar(select(Admin).where(Admin.email == email))
        if existing:
            existing.role = 'SUPER_ADMIN'
            existing.full_name = full_name
            existing.password_hash = get_password_hash(password)
            existing.is_active = True
            db.add(existing)
            db.commit()
            print(f'[seed_admin] Updated SUPER_ADMIN: {email}')
            return

        admin = Admin(
            email=email,
            password_hash=get_password_hash(password),
            full_name=full_name,
            role='SUPER_ADMIN',
            is_active=True,
        )
        db.add(admin)
        db.commit()
        print(f'[seed_admin] Created SUPER_ADMIN: {email}')


if __name__ == '__main__':
    main()
