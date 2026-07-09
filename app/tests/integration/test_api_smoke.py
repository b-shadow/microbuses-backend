from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_healthcheck_ok():
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json()['status'] == 'ok'


def test_auth_me_without_token_requires_auth():
    response = client.get('/api/v1/auth/me')
    assert response.status_code == 401


def test_active_trips_current_requires_auth_token():
    response = client.get('/api/v1/active-trips/current')
    assert response.status_code in (401, 403)

