import logging
from datetime import datetime, timezone

from app.db.client import get_supabase
from app.repositories import execute_or_503

logger = logging.getLogger(__name__)

_memory_trust: dict[tuple[str, str], dict] = {}
_memory_memory: dict[tuple[str, str], dict] = {}


def apply_npc_state_updates(session_id: str, updates: list[dict]) -> None:
    now = datetime.now(timezone.utc).isoformat()
    supabase = get_supabase()

    for update in updates:
        npc_id = update["npc_id"]
        trust_row = {
            "simulation_session_id": session_id,
            "npc_id": npc_id,
            "trust_score": update["trust_score"],
            "sentiment": update["sentiment"],
            "updated_at": now,
        }
        if not supabase:
            _memory_trust[(session_id, npc_id)] = trust_row
        else:
            execute_or_503(
                supabase.table("stakeholder_trust")
                .upsert(trust_row, on_conflict="simulation_session_id,npc_id")
            )

        if update.get("memory_summary") is not None:
            memory_row = {
                "simulation_session_id": session_id,
                "npc_id": npc_id,
                "memory_summary": update["memory_summary"],
                "updated_at": now,
            }
            if not supabase:
                _memory_memory[(session_id, npc_id)] = memory_row
            else:
                execute_or_503(
                    supabase.table("npc_memory")
                    .upsert(memory_row, on_conflict="simulation_session_id,npc_id")
                )


def get_trust(session_id: str) -> list[dict]:
    supabase = get_supabase()
    if not supabase:
        return [row for (sid, _), row in _memory_trust.items() if sid == session_id]
    result = execute_or_503(
        supabase.table("stakeholder_trust").select("*").eq("simulation_session_id", session_id)
    )
    return result.data


def get_memory(session_id: str) -> list[dict]:
    supabase = get_supabase()
    if not supabase:
        return [row for (sid, _), row in _memory_memory.items() if sid == session_id]
    result = execute_or_503(
        supabase.table("npc_memory").select("*").eq("simulation_session_id", session_id)
    )
    return result.data
