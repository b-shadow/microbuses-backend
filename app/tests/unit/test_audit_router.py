from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.core.exceptions import AppException
from app.modules.audit.router import get_audit_detail, get_audit_logs


class DummyDb:
    def __init__(self, row=None):
        self._row = row

    def get(self, model, audit_id):
        return self._row


class Driver:
    def __init__(self, actor_id):
        self.id = actor_id


def test_get_audit_logs_allows_driver_and_filters_own_rows(monkeypatch):
    driver_id = uuid4()
    actor = Driver(driver_id)
    captured = {}

    def fake_list_logs(db, limit=100, actor_id=None):
        captured['actor_id'] = actor_id
        return []

    monkeypatch.setattr('app.modules.audit.router.list_logs', fake_list_logs)

    response = get_audit_logs(actor=actor, db=DummyDb())

    assert response.success is True
    assert response.data == []
    assert captured['actor_id'] == driver_id


def test_get_audit_detail_blocks_driver_for_foreign_row():
    driver_id = uuid4()
    other_id = uuid4()
    actor = Driver(driver_id)
    row = SimpleNamespace(id=uuid4(), actor_id=other_id, detail={}, action='TRIP_STARTED', entity='ACTIVE_TRIP')

    with pytest.raises(AppException) as exc:
        get_audit_detail(str(row.id), actor=actor, db=DummyDb(row=row))

    assert exc.value.status_code == 403
    assert exc.value.error_code == 'FORBIDDEN'


def test_get_audit_detail_allows_driver_for_own_row():
    driver_id = uuid4()
    actor = Driver(driver_id)
    row = SimpleNamespace(id=uuid4(), actor_id=driver_id, detail={'ok': True}, action='TRIP_STARTED', entity='ACTIVE_TRIP')

    response = get_audit_detail(str(row.id), actor=actor, db=DummyDb(row=row))

    assert response.success is True
    assert response.data['id'] == str(row.id)
    assert response.data['detail'] == {'ok': True}
