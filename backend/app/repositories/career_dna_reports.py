import logging
from typing import Optional

from app.db.client import get_supabase
from app.repositories import execute_or_503

logger = logging.getLogger(__name__)

_memory_reports: dict[str, dict] = {}


def save_report(report_data: dict) -> dict:
    supabase = get_supabase()
    if not supabase:
        _memory_reports[report_data["id"]] = report_data
        return report_data
    result = execute_or_503(supabase.table("career_dna_reports").insert(report_data))
    return result.data[0]


def get_report(report_id: str) -> Optional[dict]:
    supabase = get_supabase()
    if not supabase:
        return _memory_reports.get(report_id)
    result = execute_or_503(
        supabase.table("career_dna_reports").select("*").eq("id", report_id).limit(1)
    )
    return result.data[0] if result.data else None


def list_reports_for_user(user_id: str) -> list[dict]:
    supabase = get_supabase()
    if not supabase:
        return [r for r in _memory_reports.values() if r["user_id"] == user_id]
    result = execute_or_503(
        supabase.table("career_dna_reports")
        .select("*")
        .eq("user_id", user_id)
        .order("generated_at", desc=True)
    )
    return result.data


def find_report_for_session(user_id: str, session_id: str) -> Optional[dict]:
    supabase = get_supabase()
    if not supabase:
        matches = [
            r
            for r in _memory_reports.values()
            if r["user_id"] == user_id
            and session_id in (r.get("simulation_session_ids") or [])
        ]
        if not matches:
            return None
        return max(matches, key=lambda r: r["generated_at"])

    result = execute_or_503(
        supabase.table("career_dna_reports")
        .select("*")
        .eq("user_id", user_id)
        .contains("simulation_session_ids", [session_id])
        .order("generated_at", desc=True)
        .limit(1)
    )
    return result.data[0] if result.data else None
