import pytest

from app.core.exceptions import AppException
from app.modules.auth.service import AuthService
from app.modules.auth.schemas import LoginRequest


class DummyActor:
    def __init__(self, role_name='USER', is_active=True, approval_status='APPROVED'):
        self.id = 'actor-id'
        self.email = 'x@test.com'
        self.password_hash = 'hashed'
        self.role = role_name
        self.is_active = is_active
        self.approval_status = approval_status


class DummyRepo:
    def __init__(self, found):
        self._found = found

    def find_by_email(self, db, email):
        return self._found


def test_login_invalid_credentials_when_email_not_found(monkeypatch):
    svc = AuthService()
    svc.repository = DummyRepo(None)

    with pytest.raises(AppException) as exc:
        svc.login(db=None, payload=LoginRequest(email='a@b.com', password='123456'))

    assert exc.value.error_code == 'INVALID_CREDENTIALS'


def test_login_rejects_inactive_account(monkeypatch):
    svc = AuthService()
    actor = DummyActor(is_active=False)
    svc.repository = DummyRepo(('USER', actor))
    monkeypatch.setattr('app.modules.auth.service.verify_password', lambda plain, hashed: True)

    with pytest.raises(AppException) as exc:
        svc.login(db=None, payload=LoginRequest(email='x@test.com', password='123456'))

    assert exc.value.error_code == 'ACCOUNT_INACTIVE'


def test_login_rejects_driver_not_approved(monkeypatch):
    svc = AuthService()
    actor = DummyActor(role_name='DRIVER', approval_status='PENDING')
    svc.repository = DummyRepo(('DRIVER', actor))
    monkeypatch.setattr('app.modules.auth.service.verify_password', lambda plain, hashed: True)

    with pytest.raises(AppException) as exc:
        svc.login(db=None, payload=LoginRequest(email='x@test.com', password='123456'))

    assert exc.value.error_code == 'DRIVER_NOT_APPROVED'


def test_login_success_returns_token(monkeypatch):
    svc = AuthService()
    actor = DummyActor(role_name='USER', is_active=True)
    svc.repository = DummyRepo(('USER', actor))
    monkeypatch.setattr('app.modules.auth.service.verify_password', lambda plain, hashed: True)

    result = svc.login(db=None, payload=LoginRequest(email='x@test.com', password='123456'))

    assert 'access_token' in result
    assert result['role'] == 'USER'
