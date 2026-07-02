import logging
from datetime import datetime, timezone
from typing import Optional

from app.db.client import get_supabase

logger = logging.getLogger(__name__)


def get_or_create_lookup(table: str, name: str) -> Optional[str]:
    """Resolves a display name to its lookup-table id, creating the row if it
    doesn't exist yet. Returns None for a blank name (no FK, e.g. university
    left empty at signup)."""
    name = (name or "").strip()
    if not name:
        return None

    supabase = get_supabase()
    existing = supabase.table(table).select("id").eq("name", name).limit(1).execute()
    if existing.data:
        return existing.data[0]["id"]

    try:
        created = supabase.table(table).insert({"name": name}).execute()
        return created.data[0]["id"]
    except Exception:
        # Lost a race with a concurrent signup creating the same name — it exists now.
        existing = supabase.table(table).select("id").eq("name", name).limit(1).execute()
        return existing.data[0]["id"]


def _flatten_user(row: dict) -> dict:
    """PostgREST embeds FK lookups as nested objects (universities/degrees) —
    flatten those back to plain display strings so callers don't need to
    know the storage is normalized."""
    row = dict(row)
    university = row.pop("universities", None)
    degree = row.pop("degrees", None)
    row["university"] = university["name"] if university else ""
    row["degree"] = degree["name"] if degree else ""
    return row


def create_user(data: dict) -> dict:
    supabase = get_supabase()
    university_name = (data.get("university") or "").strip()
    degree_name = (data.get("degree") or "").strip()
    university_id = get_or_create_lookup("universities", university_name)
    degree_id = get_or_create_lookup("degrees", degree_name)

    result = supabase.table("users").insert({
        "email": data["email"],
        "password_hash": data["password_hash"],
        "full_name": data["full_name"],
        "university_id": university_id,
        "degree_id": degree_id,
        "graduation_year": data.get("graduation_year"),
        "core_interests": data.get("core_interests", []),
    }).execute()

    user = result.data[0]
    user["university"] = university_name
    user["degree"] = degree_name
    return user


def get_user_by_email(email: str) -> Optional[dict]:
    supabase = get_supabase()
    result = (
        supabase.table("users")
        .select("*, universities(name), degrees(name)")
        .eq("email", email)
        .limit(1)
        .execute()
    )
    return _flatten_user(result.data[0]) if result.data else None


def get_user_by_id(user_id: str) -> Optional[dict]:
    supabase = get_supabase()
    result = (
        supabase.table("users")
        .select("*, universities(name), degrees(name)")
        .eq("id", user_id)
        .limit(1)
        .execute()
    )
    return _flatten_user(result.data[0]) if result.data else None


def update_last_login(user_id: str) -> None:
    supabase = get_supabase()
    supabase.table("users").update({
        "last_login": datetime.now(timezone.utc).isoformat(),
        "failed_login_attempts": 0,
        "locked_until": None,
    }).eq("id", user_id).execute()


def record_failed_login(user_id: str, attempts: int, locked_until: Optional[str]) -> None:
    supabase = get_supabase()
    supabase.table("users").update({
        "failed_login_attempts": attempts,
        "locked_until": locked_until,
    }).eq("id", user_id).execute()


def save_refresh_token(user_id: str, token_hash: str, expires_at: str) -> str:
    supabase = get_supabase()
    result = supabase.table("refresh_tokens").insert({
        "user_id": user_id,
        "token_hash": token_hash,
        "expires_at": expires_at,
    }).execute()
    return result.data[0]["id"]


def get_refresh_token_by_hash(token_hash: str) -> Optional[dict]:
    supabase = get_supabase()
    result = (
        supabase.table("refresh_tokens")
        .select("*")
        .eq("token_hash", token_hash)
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else None


def revoke_refresh_token(token_id: str, replaced_by: Optional[str] = None) -> None:
    supabase = get_supabase()
    update = {"revoked_at": datetime.now(timezone.utc).isoformat()}
    if replaced_by:
        update["replaced_by"] = replaced_by
    supabase.table("refresh_tokens").update(update).eq("id", token_id).execute()


def revoke_all_user_tokens(user_id: str) -> None:
    supabase = get_supabase()
    supabase.table("refresh_tokens").update({
        "revoked_at": datetime.now(timezone.utc).isoformat()
    }).eq("user_id", user_id).is_("revoked_at", "null").execute()
