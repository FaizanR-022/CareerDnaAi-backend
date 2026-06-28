import logging
from typing import Optional

from fastapi import Header, HTTPException

from app.db.client import get_supabase

logger = logging.getLogger(__name__)


async def get_current_user(authorization: Optional[str] = Header(None)) -> dict:
    """
    Validates Supabase JWT from Authorization header.
    Falls back to a test user if Supabase is not configured (dev mode).
    """
    supabase = get_supabase()

    if not supabase:
        return {"user_id": "dev-user-001", "email": "dev@test.com"}

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    token = authorization.split(" ")[1]
    try:
        user = supabase.auth.get_user(token)
        return {"user_id": user.user.id, "email": user.user.email}
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")


def verify_session_ownership(state: dict, current_user: dict) -> None:
    if state["user_id"] != current_user["user_id"] and current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Not your session")
