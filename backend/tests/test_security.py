"""
Test Suite — core/security.py
Password hashing, JWT access tokens, refresh token generation/hashing.
No DB required.

Run: pytest tests/test_security.py
"""
import time

import jwt
import pytest

from app.core.config import get_settings
from app.core.security import (
    BCRYPT_MAX_BYTES,
    create_access_token,
    decode_access_token,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)


@pytest.fixture(autouse=True)
def jwt_settings(monkeypatch):
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-key-for-pytest-only")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_hash_password_round_trip():
    hashed = hash_password("correct-horse-battery-staple")
    assert hashed != "correct-horse-battery-staple"
    assert verify_password("correct-horse-battery-staple", hashed)


def test_verify_password_rejects_wrong_password():
    hashed = hash_password("correct-horse-battery-staple")
    assert not verify_password("wrong-password", hashed)


def test_hash_password_unique_salts():
    h1 = hash_password("same-password")
    h2 = hash_password("same-password")
    assert h1 != h2  # bcrypt salts each hash differently
    assert verify_password("same-password", h1)
    assert verify_password("same-password", h2)


def test_bcrypt_max_bytes_boundary():
    # bcrypt silently truncates beyond 72 bytes — confirms the boundary this
    # app relies on (schemas/auth.py rejects longer passwords outright rather
    # than trusting this truncation).
    long_password = "a" * (BCRYPT_MAX_BYTES + 20)
    hashed = hash_password(long_password[:BCRYPT_MAX_BYTES])
    assert verify_password(long_password[:BCRYPT_MAX_BYTES], hashed)


def test_create_and_decode_access_token():
    token = create_access_token("user-123", "student@example.com", "student")
    payload = decode_access_token(token)

    assert payload["sub"] == "user-123"
    assert payload["email"] == "student@example.com"
    assert payload["role"] == "student"
    assert payload["type"] == "access"


def test_decode_access_token_rejects_bad_signature():
    token = create_access_token("user-123", "student@example.com", "student")
    tampered = token[:-4] + "abcd"  # corrupt the signature

    with pytest.raises(jwt.InvalidTokenError):
        decode_access_token(tampered)


def test_decode_access_token_rejects_expired_token(monkeypatch):
    monkeypatch.setattr(get_settings(), "access_token_expire_minutes", -1)
    token = create_access_token("user-123", "student@example.com", "student")

    with pytest.raises(jwt.ExpiredSignatureError):
        decode_access_token(token)


def test_generate_refresh_token_shape():
    raw, token_hash, expires_at = generate_refresh_token()

    assert raw != token_hash
    assert token_hash == hash_refresh_token(raw)
    assert expires_at.tzinfo is not None


def test_generate_refresh_token_unique():
    raw1, _, _ = generate_refresh_token()
    raw2, _, _ = generate_refresh_token()
    assert raw1 != raw2


def test_hash_refresh_token_deterministic():
    raw = "some-raw-refresh-token-value"
    assert hash_refresh_token(raw) == hash_refresh_token(raw)
