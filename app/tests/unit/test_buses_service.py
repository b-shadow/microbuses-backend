from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from app.core.exceptions import AppException
from app.modules.buses.schemas import BusChangeLineRequest, BusCreateRequest
from app.modules.buses.service import BusesService


class DummyDb:
    def __init__(self):
        self.scalar = Mock()
        self.get = Mock()
        self.add = Mock()
        self.flush = Mock()
        self.commit = Mock()
        self.refresh = Mock()


def test_create_bus_rejects_duplicate_plate():
    db = DummyDb()
    db.scalar.return_value = object()
    svc = BusesService()

    payload = BusCreateRequest(
        plate='123ABC',
        model='Toyota',
        seats_count=20,
        internal_number='10',
        current_line_id=1,
    )

    with pytest.raises(AppException) as exc:
        svc.create_bus(db, payload, actor=SimpleNamespace(id='a1', __class__=SimpleNamespace(__name__='Admin')))

    assert exc.value.error_code == 'PLATE_ALREADY_EXISTS'


def test_create_bus_rejects_missing_line():
    db = DummyDb()
    db.scalar.return_value = None
    db.get.return_value = None
    svc = BusesService()

    payload = BusCreateRequest(
        plate='123ABC',
        model='Toyota',
        seats_count=20,
        internal_number='10',
        current_line_id=1,
    )

    with pytest.raises(AppException) as exc:
        svc.create_bus(db, payload, actor=SimpleNamespace(id='a1', __class__=SimpleNamespace(__name__='Admin')))

    assert exc.value.error_code == 'LINE_NOT_FOUND'


def test_change_line_sets_inactive_for_line_zero(monkeypatch):
    db = DummyDb()
    bus = SimpleNamespace(id='b1', current_line_id=5, status='ACTIVE')
    line_zero = SimpleNamespace(code='0', is_active=True)

    svc = BusesService()
    svc.get_bus = Mock(return_value=bus)
    db.get.return_value = line_zero

    monkeypatch.setattr('app.modules.buses.service.log_event', lambda *args, **kwargs: None)

    out = svc.change_line(
        db,
        'b1',
        BusChangeLineRequest(line_id=0),
        actor=SimpleNamespace(id='a1', __class__=SimpleNamespace(__name__='Admin')),
    )

    assert out.status == 'INACTIVE'
    assert out.current_line_id == 0
    db.commit.assert_called_once()
