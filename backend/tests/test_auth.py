"""
Test Suite — Auth (signup / signin / refresh / logout)
Exercises app.services.auth_service against an in-memory fake of
app.repositories.auth, so no real Supabase connection is required.

Run: pytest tests/test_auth.py
"""

import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest

from app.core.config import get_settings


@pytest.fixture(autouse=True)
def jwt_settings(monkeypatch):
    """create_access_token/decode_access_token need a configured secret."""
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-key-for-pytest-only")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


class FakeDB:
    """In-memory stand-in for the users / refresh_tokens tables."""

    def __init__(self):
        self.users = {}
        self.refresh_tokens = {}
        self._next_id = 1

    def new_id(self) -> str:
        val = str(self._next_id)
        self._next_id += 1
        return val


@pytest.fixture
def fake_db(monkeypatch):
    db = FakeDB()

    def create_user(data):
        user_id = db.new_id()
        user = {
            "id": user_id,
            "email": data["email"],
            "password_hash": data["password_hash"],
            "full_name": data["full_name"],
            "role": "student",
            "university": data.get("university", ""),
            "degree": data.get("degree", ""),
            "graduation_year": data.get("graduation_year"),
            "core_interests": data.get("core_interests", []),
            "is_active": True,
            "failed_login_attempts": 0,
            "locked_until": None,
        }
        db.users[user_id] = user
        return user

    def get_user_by_email(email):
        return next((u for u in db.users.values() if u["email"] == email), None)

    def get_user_by_id(user_id):
        return db.users.get(user_id)

    def update_last_login(user_id):
        db.users[user_id]["failed_login_attempts"] = 0
        db.users[user_id]["locked_until"] = None

    def record_failed_login(user_id, attempts, locked_until):
        db.users[user_id]["failed_login_attempts"] = attempts
        db.users[user_id]["locked_until"] = locked_until

    def save_refresh_token(user_id, token_hash, expires_at):
        token_id = db.new_id()
        db.refresh_tokens[token_id] = {
            "id": token_id,
            "user_id": user_id,
            "token_hash": token_hash,
            "expires_at": expires_at,
            "revoked_at": None,
            "replaced_by": None,
        }
        return token_id

    def get_refresh_token_by_hash(token_hash):
        return next(
            (t for t in db.refresh_tokens.values() if t["token_hash"] == token_hash), None
        )

    def revoke_refresh_token(token_id, replaced_by=None):
        db.refresh_tokens[token_id]["revoked_at"] = datetime.now(timezone.utc).isoformat()
        if replaced_by:
            db.refresh_tokens[token_id]["replaced_by"] = replaced_by

    def revoke_all_user_tokens(user_id):
        for t in db.refresh_tokens.values():
            if t["user_id"] == user_id and not t["revoked_at"]:
                t["revoked_at"] = datetime.now(timezone.utc).isoformat()

    import app.repositories.auth as auth_repo

    monkeypatch.setattr(auth_repo, "create_user", create_user)
    monkeypatch.setattr(auth_repo, "get_user_by_email", get_user_by_email)
    monkeypatch.setattr(auth_repo, "get_user_by_id", get_user_by_id)
    monkeypatch.setattr(auth_repo, "update_last_login", update_last_login)
    monkeypatch.setattr(auth_repo, "record_failed_login", record_failed_login)
    monkeypatch.setattr(auth_repo, "save_refresh_token", save_refresh_token)
    monkeypatch.setattr(auth_repo, "get_refresh_token_by_hash", get_refresh_token_by_hash)
    monkeypatch.setattr(auth_repo, "revoke_refresh_token", revoke_refresh_token)
    monkeypatch.setattr(auth_repo, "revoke_all_user_tokens", revoke_all_user_tokens)

    return db


SIGNUP_DATA = {
    "email": "student@example.com",
    "password": "correct-horse-battery-staple",
    "full_name": "Jane Doe",
    "university": "MIT",
    "degree": "CS",
    "graduation_year": 2026,
    "core_interests": ["backend", "ml"],
}


def test_verify_self_or_admin_allows_self():
    from app.core.auth import verify_self_or_admin

    verify_self_or_admin("user-1", {"user_id": "user-1", "role": "student"})  # no raise


def test_verify_self_or_admin_allows_admin():
    from app.core.auth import verify_self_or_admin

    verify_self_or_admin("someone-else", {"user_id": "admin-1", "role": "admin"})  # no raise


def test_verify_self_or_admin_blocks_other_non_admin():
    from fastapi import HTTPException

    from app.core.auth import verify_self_or_admin

    with pytest.raises(HTTPException) as exc_info:
        verify_self_or_admin("someone-else", {"user_id": "user-1", "role": "student"})
    assert exc_info.value.status_code == 403


def test_get_user_profile_returns_own_profile(fake_db):
    from app.services import auth_service

    signup_result = auth_service.signup(dict(SIGNUP_DATA))
    user_id = signup_result["user"]["id"]

    profile = auth_service.get_user_profile(user_id)

    assert profile["email"] == SIGNUP_DATA["email"]
    assert profile["university"] == SIGNUP_DATA["university"]
    assert "password_hash" not in profile


def test_get_user_profile_404_for_missing_user(fake_db):
    from fastapi import HTTPException

    from app.services import auth_service

    with pytest.raises(HTTPException) as exc_info:
        auth_service.get_user_profile("does-not-exist")
    assert exc_info.value.status_code == 404


def test_signup_creates_user_and_issues_tokens(fake_db):
    from app.services import auth_service

    result = auth_service.signup(dict(SIGNUP_DATA))

    assert result["access_token"]
    assert result["refresh_token"]
    assert result["user"]["email"] == SIGNUP_DATA["email"]
    assert result["user"]["role"] == "student"
    assert "password" not in result["user"]
    assert "password_hash" not in result["user"]


def test_signup_rejects_duplicate_email(fake_db):
    from fastapi import HTTPException

    from app.services import auth_service

    auth_service.signup(dict(SIGNUP_DATA))

    with pytest.raises(HTTPException) as exc_info:
        auth_service.signup(dict(SIGNUP_DATA))

    assert exc_info.value.status_code == 409


def test_signin_success(fake_db):
    from app.services import auth_service

    auth_service.signup(dict(SIGNUP_DATA))
    result = auth_service.signin(SIGNUP_DATA["email"], SIGNUP_DATA["password"])

    assert result["access_token"]
    assert result["user"]["email"] == SIGNUP_DATA["email"]


def test_signin_wrong_password_rejected(fake_db):
    from fastapi import HTTPException

    from app.services import auth_service

    auth_service.signup(dict(SIGNUP_DATA))

    with pytest.raises(HTTPException) as exc_info:
        auth_service.signin(SIGNUP_DATA["email"], "wrong-password")

    assert exc_info.value.status_code == 401


def test_signin_locks_account_after_max_failed_attempts(fake_db):
    from fastapi import HTTPException

    from app.services import auth_service

    auth_service.signup(dict(SIGNUP_DATA))

    for _ in range(auth_service.MAX_FAILED_ATTEMPTS):
        with pytest.raises(HTTPException):
            auth_service.signin(SIGNUP_DATA["email"], "wrong-password")

    with pytest.raises(HTTPException) as exc_info:
        auth_service.signin(SIGNUP_DATA["email"], SIGNUP_DATA["password"])

    assert exc_info.value.status_code == 423


def test_refresh_rotates_token(fake_db):
    from app.services import auth_service

    signup_result = auth_service.signup(dict(SIGNUP_DATA))
    old_refresh = signup_result["refresh_token"]

    refreshed = auth_service.refresh(old_refresh)

    assert refreshed["refresh_token"] != old_refresh
    assert refreshed["access_token"]


def test_reused_refresh_token_revokes_all_sessions(fake_db):
    from fastapi import HTTPException

    from app.services import auth_service

    signup_result = auth_service.signup(dict(SIGNUP_DATA))
    old_refresh = signup_result["refresh_token"]

    refreshed = auth_service.refresh(old_refresh)  # rotates; old_refresh now revoked

    with pytest.raises(HTTPException) as exc_info:
        auth_service.refresh(old_refresh)
    assert exc_info.value.status_code == 401

    # Reuse detection revokes the whole chain, including the newest token
    with pytest.raises(HTTPException):
        auth_service.refresh(refreshed["refresh_token"])


def test_logout_revokes_refresh_token(fake_db):
    from fastapi import HTTPException

    from app.services import auth_service

    signup_result = auth_service.signup(dict(SIGNUP_DATA))
    refresh_token = signup_result["refresh_token"]

    auth_service.logout(refresh_token)

    with pytest.raises(HTTPException) as exc_info:
        auth_service.refresh(refresh_token)
    assert exc_info.value.status_code == 401


def test_logout_on_one_session_does_not_revoke_other_sessions(fake_db):
    """A directly-revoked (logout) token must not trigger reuse-detection's
    cascade — only a token superseded by rotation should kill the whole chain.
    Otherwise logging out on one device would silently kill every other device."""
    from app.services import auth_service

    auth_service.signup(dict(SIGNUP_DATA))
    session_a = auth_service.signin(SIGNUP_DATA["email"], SIGNUP_DATA["password"])
    session_b = auth_service.signin(SIGNUP_DATA["email"], SIGNUP_DATA["password"])

    auth_service.logout(session_a["refresh_token"])

    # Session B must still be able to refresh — logging out A shouldn't touch it.
    refreshed_b = auth_service.refresh(session_b["refresh_token"])
    assert refreshed_b["access_token"]
