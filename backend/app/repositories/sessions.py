import json
import logging
from typing import Optional

from app.db.client import get_supabase

logger = logging.getLogger(__name__)

# In-memory fallback used when Supabase is not configured (local dev without .env)
_memory_sessions: dict = {}


def save_session(session_id: str, state: dict) -> None:
    supabase = get_supabase()
    if supabase:
        try:
            supabase.table("sessions").upsert({
                "id": session_id,
                "user_id": state["user_id"],
                "domain": state["domain"],
                "difficulty": state["difficulty"],
                "status": state["session_status"],
                "current_scene_id": state["current_scene_id"],
                "scenes_completed": state["scenes_completed"],
                "scene_state": {
                    "scores": state["scores"],
                    "decisions_log": state["decisions_log"],
                    "stakeholder_trust": state["stakeholder_trust"],
                    "npc_states": state["npc_states"],
                    "sprint_progress": state["sprint_progress"],
                },
                "sprint_progress": state["sprint_progress"],
                "last_active_at": "now()",  # known issue: stores literal string — see team notes
            }).execute()
        except Exception as e:
            logger.error(f"Supabase save error: {e} — falling back to memory")
            _memory_sessions[session_id] = state
    else:
        _memory_sessions[session_id] = state


def load_session(session_id: str) -> Optional[dict]:
    supabase = get_supabase()
    if supabase:
        try:
            result = (
                supabase.table("sessions")
                .select("*")
                .eq("id", session_id)
                .single()
                .execute()
            )
            if result.data:
                row = result.data
                scene_state = row.get("scene_state") or {}
                if isinstance(scene_state, str):
                    scene_state = json.loads(scene_state)

                from app.agents.director import create_initial_state
                state = create_initial_state(
                    session_id, row["user_id"], row["domain"], row["difficulty"]
                )
                state["current_scene_id"] = row["current_scene_id"]
                state["scenes_completed"] = row["scenes_completed"] or []
                state["session_status"] = row["status"]
                state["sprint_progress"] = row.get("sprint_progress", 0)
                state["scores"] = scene_state.get("scores", state["scores"])
                state["decisions_log"] = scene_state.get("decisions_log", [])
                state["stakeholder_trust"] = scene_state.get("stakeholder_trust", state["stakeholder_trust"])
                state["npc_states"] = scene_state.get("npc_states", state["npc_states"])
                return state
        except Exception as e:
            logger.error(f"Supabase load error: {e}")

    return _memory_sessions.get(session_id)


def get_incomplete_sessions(user_id: str) -> list:
    supabase = get_supabase()
    if not supabase:
        return [
            {"session_id": sid, "domain": s["domain"], "status": s["session_status"]}
            for sid, s in _memory_sessions.items()
            if s["user_id"] == user_id and s["session_status"] in ("active", "paused")
        ]

    result = (
        supabase.table("sessions")
        .select("id, domain, difficulty, status, current_scene_id, started_at, last_active_at")
        .eq("user_id", user_id)
        .in_("status", ["active", "paused"])
        .execute()
    )
    return result.data
