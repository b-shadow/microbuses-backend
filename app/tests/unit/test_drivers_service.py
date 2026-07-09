from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from app.core.exceptions import AppException
from app.modules.drivers.schemas import DriverCreateRequest, DriverDecisionRequest
from app.modules.drivers.service import DriversService


class DummyDb:
    def __init__(self):
        self.scalar = Mock()
        self.get = Mock()
        self.add = Mock()
        self.commit = Mock()
        self.refresh = Mock()


def test_create_driver_rejects_duplicate_email():
    db = DummyDb()
    db.scalar.side_effect = [object()]
    svc = DriversService()

    payload = DriverCreateRequest(
        email='driver@test.com',
        password='StrongPass123',
        ci='1234567',
        full_name='Driver One',
        phone='70000000',
        license_category='B',
    )

    with pytest.raises(AppException) as exc:
        svc.create_driver(db, payload)

    assert exc.value.error_code == 'EMAIL_ALREADY_EXISTS'


def test_create_driver_rejects_duplicate_ci():
    db = DummyDb()
    db.scalar.side_effect = [None, object()]
    svc = DriversService()

    payload = DriverCreateRequest(
        email='driver@test.com',
        password='StrongPass123',
        ci='1234567',
        full_name='Driver One',
        phone='70000000',
        license_category='B',
    )

    with pytest.raises(AppException) as exc:
        svc.create_driver(db, payload)

    assert exc.value.error_code == 'CI_ALREADY_EXISTS'


def test_set_status_updates_driver_and_commits():
    db = DummyDb()
    driver = SimpleNamespace(id='d1', approval_status='PENDING')

    svc = DriversService()
    svc.get_driver = Mock(return_value=driver)
    svc._audit = Mock()

    actor = SimpleNamespace(id='a1', __class__=SimpleNamespace(__name__='Admin'))
    decision = DriverDecisionRequest(reason='valid docs')

    out = svc.set_status(db, 'd1', 'APPROVED', actor, decision)

    assert out.approval_status == 'APPROVED'
    db.commit.assert_called_once()
    svc._audit.assert_called_once()
