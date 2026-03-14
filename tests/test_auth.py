from app.services.auth import hash_api_key


def test_hash_api_key_is_deterministic():
    key = "abc123"
    assert hash_api_key(key) == hash_api_key(key)
