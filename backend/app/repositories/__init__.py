import logging

from fastapi import HTTPException

logger = logging.getLogger(__name__)


def execute_or_503(query):
    """Runs a Supabase query. A real failure (Supabase configured but the
    call raised) becomes a 503 instead of silently falling back to memory —
    so a live-DB outage is visible to the caller instead of looking like a
    successful save."""
    try:
        return query.execute()
    except Exception as e:
        logger.error(f"Supabase query failed: {e}")
        raise HTTPException(status_code=503, detail="Database temporarily unavailable") from e
