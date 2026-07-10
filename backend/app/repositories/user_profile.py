import logging
from typing import Optional

from app.db.client import get_supabase
from app.repositories import execute_or_503

logger = logging.getLogger(__name__)


def get_self_rating(user_id: str, domain: str) -> Optional[int]:
    supabase = get_supabase()
    if not supabase:
        return None
    column = f"self_rated_{domain}"
    result = execute_or_503(
        supabase.table("user_profiles").select(column).eq("user_id", user_id).limit(1)
    )
    return result.data[0][column] if result.data else None
