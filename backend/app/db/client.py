import logging
from typing import Optional

from app.core.config import get_settings

logger = logging.getLogger(__name__)

_supabase = None


def init_supabase():
    global _supabase
    settings = get_settings()

    if (
        settings.supabase_url.startswith("https://")
        and settings.supabase_key
        and not settings.supabase_key.startswith("your_")
    ):
        from supabase import create_client
        _supabase = create_client(settings.supabase_url, settings.supabase_key)
        logger.info("Supabase connected")
    else:
        logger.warning("Supabase not configured — running in memory-only mode")

    return _supabase


def get_supabase() -> Optional[object]:
    return _supabase
