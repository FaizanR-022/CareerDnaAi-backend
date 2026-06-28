import logging

from app.db.client import get_supabase

logger = logging.getLogger(__name__)


def save_onboarding(user_id: str, data: dict) -> None:
    supabase = get_supabase()

    supabase.table("users").update({
        "university": data["university"],
    }).eq("id", user_id).execute()

    supabase.table("user_profiles").upsert({
        "user_id": user_id,
        "personality_results": data["personality_results"],
        "interest_results": data["career_interests"],
        "self_rated_pm": data["self_rated_pm"],
        "self_rated_sqa": data["self_rated_sqa"],
        "self_rated_data": data["self_rated_data"],
        "self_rated_frontend": data["self_rated_frontend"],
        "self_rated_backend": data["self_rated_backend"],
    }).execute()
