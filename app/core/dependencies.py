from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool

from app.core.security import decode_token_safe
from app.core.settings import get_settings
from app.modules.admins.models import Admin
from app.modules.drivers.models import Driver
from app.modules.users.models import User

settings = get_settings()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.api_prefix}/auth/login")
engine = create_engine(
    settings.database_url,
    future=True,
    poolclass=NullPool,
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_actor(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    payload = decode_token_safe(token)
    if not payload:
        return None
    role = payload.get('role')
    subject = payload.get('sub')
    if not role or not subject:
        return None
    if role == 'USER':
        return db.get(User, subject)
    if role in {'ADMIN', 'SUPER_ADMIN'}:
        return db.get(Admin, subject)
    if role == 'DRIVER':
        return db.get(Driver, subject)
    return None