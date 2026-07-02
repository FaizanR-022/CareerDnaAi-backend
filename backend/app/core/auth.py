import logging
from typing import Optional

import jwt
from fastapi import Header, HTTPException

from app.core.config import get_settings
from app.core.security import decode_access_token

logger = logging.getLogger(__name__)


async def get_current_user(authorization: Optional[str] = Header(None)) -> dict:
    """
    Validates our own JWT access token from the Authorization header.
    Falls back to a test user if JWT_SECRET_KEY is not configured (dev mode).
    """
    settings = get_settings()

    if not settings.jwt_secret_key:
        return {"user_id": "dev-user-001", "email": "dev@test.com", "role": "student"}

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    token = authorization.split(" ")[1]
    try:
        payload = decode_access_token(token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

    return {"user_id": payload["sub"], "email": payload["email"], "role": payload["role"]}


def verify_self_or_admin(target_user_id: str, current_user: dict, detail: str = "Forbidden") -> None:
    if target_user_id != current_user["user_id"] and current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail=detail)


def verify_session_ownership(state: dict, current_user: dict) -> None:
    verify_self_or_admin(state["user_id"], current_user, detail="Not your session")
