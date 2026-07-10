import logging
from datetime import datetime, timezone
from typing import Optional

from app.db.client import get_supabase
from app.repositories import execute_or_503

logger = logging.getLogger(__name__)

_memory_scenes: dict[str, dict] = {}


def save_scene(scene_id: str, session_id: str, scene_number: int, content: dict) -> dict:
    row = {
        "id": scene_id,
        "simulation_session_id": session_id,
        "scene_number": scene_number,
        "content": content,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    supabase = get_supabase()
    if not supabase:
        _memory_scenes[scene_id] = row
        return row
    result = execute_or_503(supabase.table("simulation_scenes").insert(row))
    return result.data[0]


def get_scene(session_id: str, scene_number: int) -> Optional[dict]:
    supabase = get_supabase()
    if not supabase:
        return next(
            (
                s for s in _memory_scenes.values()
                if s["simulation_session_id"] == session_id and s["scene_number"] == scene_number
            ),
            None,
        )
    result = execute_or_503(
        supabase.table("simulation_scenes")
        .select("*")
        .eq("simulation_session_id", session_id)
        .eq("scene_number", scene_number)
        .limit(1)
    )
    return result.data[0] if result.data else None


def get_latest_scene(session_id: str) -> Optional[dict]:
    supabase = get_supabase()
    if not supabase:
        scenes = [s for s in _memory_scenes.values() if s["simulation_session_id"] == session_id]
        return max(scenes, key=lambda s: s["scene_number"]) if scenes else None
    result = execute_or_503(
        supabase.table("simulation_scenes")
        .select("*")
        .eq("simulation_session_id", session_id)
        .order("scene_number", desc=True)
        .limit(1)
    )
    return result.data[0] if result.data else None


def list_scenes(session_id: str) -> list[dict]:
    supabase = get_supabase()
    if not supabase:
        scenes = [s for s in _memory_scenes.values() if s["simulation_session_id"] == session_id]
        return sorted(scenes, key=lambda s: s["scene_number"])
    result = execute_or_503(
        supabase.table("simulation_scenes")
        .select("*")
        .eq("simulation_session_id", session_id)
        .order("scene_number")
    )
    return result.data
