from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.settings import get_settings

# pbkdf2_sha256 evita incompatibilidades nativas de bcrypt en algunos entornos Windows.
pwd_context = CryptContext(schemes=['pbkdf2_sha256'], deprecated='auto')
settings = get_settings()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(subject: str, role: str, expires_minutes: int | None = None) -> str:
    minutes = expires_minutes or settings.jwt_access_token_minutes
    expire = datetime.now(UTC) + timedelta(minutes=minutes)
    payload: dict[str, Any] = {'sub': subject, 'role': role, 'exp': expire}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])


def decode_token_safe(token: str) -> dict[str, Any] | None:
    try:
        return decode_token(token)
    except JWTError:
        return None

