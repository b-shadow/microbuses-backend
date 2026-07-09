from app.core.security import create_access_token, decode_token, get_password_hash, verify_password


def test_password_hash_and_verify_roundtrip():
    raw = 'MyPassword123!'
    hashed = get_password_hash(raw)
    assert hashed != raw
    assert verify_password(raw, hashed)


def test_create_and_decode_token_contains_claims():
    token = create_access_token(subject='abc-123', role='USER', expires_minutes=5)
    payload = decode_token(token)
    assert payload['sub'] == 'abc-123'
    assert payload['role'] == 'USER'
    assert 'exp' in payload
