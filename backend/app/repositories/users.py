import logging

from app.db.client import get_supabase
from app.repositories.auth import _flatten_user, get_or_create_lookup

logger = logging.getLogger(__name__)


def save_onboarding(user_id: str, data: dict) -> None:
    supabase = get_supabase()

    supabase.table("users").update({
        "university_id": get_or_create_lookup("universities", data["university"]),
    }).eq("id", user_id).execute()

    # self_rated_* columns are deliberately omitted here — they default to 3
    # in the DB (see schema.sql) and are no longer collected from the client;
    # omitting them (rather than sending 3 explicitly) means an existing
    # user's previously-set values are never overwritten by a later
    # onboarding-related update, only a brand-new row gets the default.
    supabase.table("user_profiles").upsert({
        "user_id": user_id,
        "personality_results": data["personality_results"],
        "interest_results": data["career_interests"],
    }).execute()


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
