import logging
from datetime import datetime, timezone
from typing import Optional

from app.db.client import get_supabase
from app.repositories import execute_or_503

logger = logging.getLogger(__name__)

_memory_sessions: dict[str, dict] = {}


def create_session(session_id: str, user_id: str, domain: str, difficulty: str) -> dict:
    now = datetime.now(timezone.utc).isoformat()
    row = {
        "id": session_id,
        "user_id": user_id,
        "domain": domain,
        "difficulty": difficulty,
        "status": "in_progress",
        "current_scene_number": 1,
        "started_at": now,
        "completed_at": None,
        "last_active_at": now,
    }
    supabase = get_supabase()
    if not supabase:
        _memory_sessions[session_id] = row
        return row
    result = execute_or_503(supabase.table("simulation_sessions").insert(row))
    return result.data[0]


def get_session(session_id: str) -> Optional[dict]:
    supabase = get_supabase()
    if not supabase:
        return _memory_sessions.get(session_id)
    result = execute_or_503(
        supabase.table("simulation_sessions").select("*").eq("id", session_id).limit(1)
    )
    return result.data[0] if result.data else None


def update_status(session_id: str, status: str, completed_at: Optional[str] = None) -> None:
    update = {"status": status}
    if completed_at:
        update["completed_at"] = completed_at

    supabase = get_supabase()
    if not supabase:
        if session_id in _memory_sessions:
            _memory_sessions[session_id].update(update)
        return
    execute_or_503(supabase.table("simulation_sessions").update(update).eq("id", session_id))


def bump_scene_number(session_id: str, scene_number: int) -> None:
    update = {
        "current_scene_number": scene_number,
        "last_active_at": datetime.now(timezone.utc).isoformat(),
    }
    supabase = get_supabase()
    if not supabase:
        if session_id in _memory_sessions:
            _memory_sessions[session_id].update(update)
        return
    execute_or_503(supabase.table("simulation_sessions").update(update).eq("id", session_id))


def touch_last_active(session_id: str) -> None:
    update = {"last_active_at": datetime.now(timezone.utc).isoformat()}
    supabase = get_supabase()
    if not supabase:
        if session_id in _memory_sessions:
            _memory_sessions[session_id].update(update)
        return
    execute_or_503(supabase.table("simulation_sessions").update(update).eq("id", session_id))


def list_sessions_for_user(user_id: str) -> list[dict]:
    supabase = get_supabase()
    if not supabase:
        return [s for s in _memory_sessions.values() if s["user_id"] == user_id]
    result = execute_or_503(
        supabase.table("simulation_sessions")
        .select("*")
        .eq("user_id", user_id)
        .order("started_at", desc=True)
    )
    return result.data

def update_difficulty(session_id: str, new_difficulty: str) -> None:
    supabase = get_supabase()
    if not supabase:
        if session_id in _memory_sessions:
            _memory_sessions[session_id]["difficulty"] = new_difficulty
        return
    execute_or_503(
        supabase.table("simulation_sessions")
        .update({"difficulty": new_difficulty})
        .eq("id", session_id)
    )
