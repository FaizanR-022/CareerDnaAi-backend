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
        try:
            from supabase import create_client
            _supabase = create_client(settings.supabase_url, settings.supabase_key)
            logger.info("Supabase connected successfully")
        except Exception as e:
            logger.warning(
                f"Supabase init failed ({e}). Running in memory-only mode.\n"
                "  SUPABASE_KEY in backend/.env must be the anon/service_role JWT (starts with eyJ).\n"
                "  Get it from: supabase.com → your project → Settings → Data API → anon key"
            )
            _supabase = None
    else:
        logger.warning("Supabase not configured — running in memory-only (dev) mode")

    return _supabase


def get_supabase() -> Optional[object]:
    return _supabase
