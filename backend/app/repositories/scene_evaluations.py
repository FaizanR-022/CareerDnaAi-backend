import logging
from datetime import datetime, timezone
from typing import Optional

from app.db.client import get_supabase
from app.repositories import execute_or_503

logger = logging.getLogger(__name__)

DIMENSION_KEYS = [
    "analytical_reasoning",
    "ambiguity_tolerance",
    "communication_clarity",
    "attention_to_detail",
    "decisiveness",
]

_memory_evaluations: dict[str, dict] = {}  # keyed by scene_id (1:1, unique)


def create_pending(evaluation_id: str, scene_id: str, user_response: dict) -> dict:
    row = {
        "id": evaluation_id,
        "scene_id": scene_id,
        "user_response": user_response,
        "evaluation": None,
        "overall_score": None,
        "behavioral_flags": None,
        "justification": None,
        "response_submitted_at": datetime.now(timezone.utc).isoformat(),
        "evaluated_at": None,
        **{key: None for key in DIMENSION_KEYS},
    }
    supabase = get_supabase()
    if not supabase:
        _memory_evaluations[scene_id] = row
        return row
    result = execute_or_503(supabase.table("scene_evaluations").insert(row))
    return result.data[0]


def save_evaluation(scene_id: str, evaluation: dict) -> dict:
    dimension_scores = evaluation.get("dimension_scores", {})
    update = {
        "evaluation": evaluation,
        "overall_score": evaluation.get("overall_score"),
        "behavioral_flags": evaluation.get("behavioral_flags", []),
        "justification": evaluation.get("justification"),
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
        **{key: dimension_scores.get(key) for key in DIMENSION_KEYS},
    }
    supabase = get_supabase()
    if not supabase:
        row = _memory_evaluations.setdefault(scene_id, {"scene_id": scene_id})
        row.update(update)
        return row
    result = execute_or_503(
        supabase.table("scene_evaluations").update(update).eq("scene_id", scene_id)
    )
    return result.data[0]


def get_evaluation(scene_id: str) -> Optional[dict]:
    supabase = get_supabase()
    if not supabase:
        return _memory_evaluations.get(scene_id)
    result = execute_or_503(
        supabase.table("scene_evaluations").select("*").eq("scene_id", scene_id).limit(1)
    )
    return result.data[0] if result.data else None


def list_evaluations_for_scenes(scene_ids: list[str]) -> list[dict]:
    if not scene_ids:
        return []
    supabase = get_supabase()
    if not supabase:
        return [_memory_evaluations[sid] for sid in scene_ids if sid in _memory_evaluations]
    result = execute_or_503(
        supabase.table("scene_evaluations").select("*").in_("scene_id", scene_ids)
    )
    return result.data
