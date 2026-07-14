import logging

from app.db.client import get_supabase
from app.repositories.auth import _flatten_user, get_or_create_lookup

logger = logging.getLogger(__name__)


def update_user(user_id: str, data: dict) -> dict:
    supabase = get_supabase()
    update = {}
    if data.get("full_name") is not None:
        update["full_name"] = data["full_name"]
    if data.get("graduation_year") is not None:
        update["graduation_year"] = data["graduation_year"]
    if data.get("core_interests") is not None:
        update["core_interests"] = data["core_interests"]
    if data.get("university") is not None:
        update["university_id"] = get_or_create_lookup("universities", data["university"])
    if data.get("degree") is not None:
        update["degree_id"] = get_or_create_lookup("degrees", data["degree"])

    if update:
        supabase.table("users").update(update).eq("id", user_id).execute()

    result = (
        supabase.table("users")
        .select("*, universities(name), degrees(name)")
        .eq("id", user_id)
        .limit(1)
        .execute()
    )
    if not result.data:
        raise ValueError(f"User not found after update: {user_id}")
    return _flatten_user(result.data[0])


def deactivate_user(user_id: str) -> None:
    supabase = get_supabase()
    supabase.table("users").update({"is_active": False}).eq("id", user_id).execute()
