import logging
from typing import Optional

from app.db.client import get_supabase

logger = logging.getLogger(__name__)


def save_report(report_data: dict) -> Optional[str]:
    supabase = get_supabase()
    if not supabase:
        return None
    try:
        result = supabase.table("career_dna_reports").insert(report_data).execute()
        return result.data[0]["id"] if result.data else None
    except Exception as e:
        logger.error(f"Report save error: {e}")
        return None
