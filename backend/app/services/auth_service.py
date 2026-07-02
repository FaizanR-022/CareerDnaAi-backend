import logging
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException

from app.core.security import (
    create_access_token,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from app.repositories import auth as auth_repo

logger = logging.getLogger(__name__)

MAX_FAILED_ATTEMPTS = 5
LOCKOUT_MINUTES = 15


def _user_response(user: dict) -> dict:
    return {
        "id": user["id"],
        "email": user["email"],
        "full_name": user["full_name"],
        "role": user["role"],
        "university": user.get("university") or "",
        "degree": user.get("degree") or "",
        "graduation_year": user.get("graduation_year"),
        "core_interests": user.get("core_interests") or [],
    }


def _issue_tokens(user: dict) -> dict:
    access_token = create_access_token(user["id"], user["email"], user["role"])
    raw_refresh, refresh_hash, expires_at = generate_refresh_token()
    auth_repo.save_refresh_token(user["id"], refresh_hash, expires_at.isoformat())
    return {
        "access_token": access_token,
        "refresh_token": raw_refresh,
        "token_type": "bearer",
        "user": _user_response(user),
    }


def signup(data: dict) -> dict:
    if auth_repo.get_user_by_email(data["email"]):
        raise HTTPException(status_code=409, detail="Email already registered")

    try:
        user = auth_repo.create_user({
            "email": data["email"],
            "password_hash": hash_password(data["password"]),
            "full_name": data["full_name"],
            "university": data.get("university", ""),
            "degree": data.get("degree", ""),
            "graduation_year": data.get("graduation_year"),
            "core_interests": data.get("core_interests", []),
        })
    except Exception as e:
        if "duplicate" in str(e).lower() or "unique" in str(e).lower():
            raise HTTPException(status_code=409, detail="Email already registered")
        raise

    return _issue_tokens(user)


def signin(email: str, password: str) -> dict:
    user = auth_repo.get_user_by_email(email)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    locked_until = user.get("locked_until")
    if locked_until and datetime.fromisoformat(locked_until) > datetime.now(timezone.utc):
        raise HTTPException(status_code=423, detail="Account temporarily locked. Try again later.")

    if not verify_password(password, user["password_hash"]):
        attempts = user.get("failed_login_attempts", 0) + 1
        lock_until = None
        if attempts >= MAX_FAILED_ATTEMPTS:
            lock_until = (datetime.now(timezone.utc) + timedelta(minutes=LOCKOUT_MINUTES)).isoformat()
        auth_repo.record_failed_login(user["id"], attempts, lock_until)
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not user.get("is_active", True):
        raise HTTPException(status_code=403, detail="Account is disabled")

    auth_repo.update_last_login(user["id"])
    return _issue_tokens(user)


def refresh(raw_refresh_token: str) -> dict:
    token_hash = hash_refresh_token(raw_refresh_token)
    token_row = auth_repo.get_refresh_token_by_hash(token_hash)

    if not token_row:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    if token_row.get("revoked_at"):
        if token_row.get("replaced_by"):
            # Reuse of a token that was superseded by rotation is a theft signal —
            # kill the whole chain. A token revoked directly (e.g. logout) is not.
            auth_repo.revoke_all_user_tokens(token_row["user_id"])
            raise HTTPException(status_code=401, detail="Refresh token reuse detected — all sessions revoked")
        raise HTTPException(status_code=401, detail="Refresh token has been revoked")

    if datetime.fromisoformat(token_row["expires_at"]) < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Refresh token expired")

    user = auth_repo.get_user_by_id(token_row["user_id"])
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    result = _issue_tokens(user)
    new_token_row = auth_repo.get_refresh_token_by_hash(hash_refresh_token(result["refresh_token"]))
    auth_repo.revoke_refresh_token(token_row["id"], replaced_by=new_token_row["id"])
    return result


def get_user_profile(user_id: str) -> dict:
    user = auth_repo.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return _user_response(user)


def logout(raw_refresh_token: str) -> None:
    token_hash = hash_refresh_token(raw_refresh_token)
    token_row = auth_repo.get_refresh_token_by_hash(token_hash)
    if token_row and not token_row.get("revoked_at"):
        auth_repo.revoke_refresh_token(token_row["id"])
