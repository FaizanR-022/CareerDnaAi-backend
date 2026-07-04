import logging
import uuid

from fastapi import HTTPException

from app.agents.director import build_director, create_initial_state
from app.repositories import sessions as sessions_repo

logger = logging.getLogger(__name__)

_director = build_director()


def start_session(user_id: str, domain: str, difficulty: str) -> dict:
    session_id = str(uuid.uuid4())
    state = create_initial_state(session_id, user_id, domain, difficulty)
    sessions_repo.save_session(session_id, state)

    opening_messages = []
    for npc_id, npc_config in state["scenario_config"].get("npcs", {}).items():
        diff_messages = npc_config.get("opening_messages", {}).get(difficulty, {})
        if diff_messages:
            for msg in diff_messages.get("messages", []):
                opening_messages.append({
                    "npc_id": npc_id,
                    "npc_name": npc_config.get("name", npc_id),
                    "channel": diff_messages.get("channel", "developer"),
                    "content": msg.get("content", ""),
                    "time_offset_minutes": msg.get("time_offset_minutes", 0),
                })

    voice_memo = None
    sara_config = state["scenario_config"].get("npcs", {}).get("sara_khan", {})
    if sara_config:
        voice_memo = sara_config.get("voice_memo", {}).get(difficulty)

    scene_config = state["scenario_config"]["scenes"].get("scene_1", {})
    diff_mods = scene_config.get("difficulty_modifiers", {}).get(difficulty, {})

    logger.info(f"Session started: {session_id} | {domain} | {difficulty} | user: {user_id}")

    return {
        "session_id": session_id,
        "domain": domain,
        "difficulty": difficulty,
        "current_scene_id": state["current_scene_id"],
        "scene_title": scene_config.get("title", ""),
        "scene_description": scene_config.get("description", ""),
        "opening_messages": opening_messages,
        "voice_memo": voice_memo,
        "sprint_board": scene_config.get("sprint_board") if diff_mods.get("sprint_capacity_visible") else None,
        "hint": diff_mods.get("hint_text") if diff_mods.get("hint_available") else None,
        "difficulty_modifiers": diff_mods,
        "status": "started",
    }


def handle_action(session_id: str, user_action: str, current_user: dict) -> dict:
    state = sessions_repo.load_session(session_id)
    if not state:
        raise HTTPException(status_code=404, detail="Session not found")

    if state["user_id"] != current_user["user_id"] and current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Not your session")

    state["user_action"] = user_action
    updated_state = _director.invoke(state)
    sessions_repo.save_session(session_id, updated_state)

    # FIX A — include difficulty_modifiers for the current scene in every response
    current_scene = updated_state["scenario_config"]["scenes"].get(
        updated_state.get("current_scene_id", "scene_1"), {}
    )
    difficulty_modifiers = current_scene.get(
        "difficulty_modifiers", {}
    ).get(updated_state.get("difficulty", "medium"), {})

    # FIX B — auto-trigger career fit scoring when simulation_complete is fired
    fit_preview = None
    for event in updated_state.get("ui_events", []):
        if isinstance(event, dict) and event.get("type") == "simulation_complete":
            try:
                from app.agents.career_fit_agent import generate_fit_report_data
                fit_preview = generate_fit_report_data(
                    current_user["user_id"],
                    [{
                        "domain": updated_state["domain"],
                        "scores": updated_state["scores"],
                        "decisions_log": updated_state["decisions_log"],
                        "session_id": session_id,
                    }]
                )
            except Exception as e:
                logger.error(f"Auto fit scoring failed: {e}")
            break

    return {
        "session_id": session_id,
        "action_type": updated_state["action_type"],
        "npc_response": updated_state.get("npc_response"),
        "npc_name": "Sara Khan",  # known issue: hardcoded — see team notes
        "score_update": updated_state.get("score_update"),
        "next_scene_id": updated_state.get("next_scene_id"),
        "session_status": updated_state["session_status"],
        "ui_events": updated_state.get("ui_events", []),
        "stakeholder_trust": updated_state["stakeholder_trust"],
        "current_scores": updated_state["scores"],
        "difficulty_modifiers": difficulty_modifiers,
        "fit_preview": fit_preview,
    }



def get_session_state(session_id: str) -> dict:
    state = sessions_repo.load_session(session_id)
    if not state:
        raise HTTPException(status_code=404, detail="Session not found")
    return {
        "session_id": session_id,
        "domain": state["domain"],
        "difficulty": state["difficulty"],
        "current_scene_id": state["current_scene_id"],
        "session_status": state["session_status"],
        "scores": state["scores"],
        "decisions_log": state["decisions_log"],
        "stakeholder_trust": state["stakeholder_trust"],
        "scenes_completed": state["scenes_completed"],
        "sprint_progress": state["sprint_progress"],
    }


def get_opening_messages(session_id: str) -> dict:
    state = sessions_repo.load_session(session_id)
    if not state:
        raise HTTPException(status_code=404, detail="Session not found")

    scene_config = state["scenario_config"]["scenes"].get(state["current_scene_id"], {})
    diff_mods = scene_config.get("difficulty_modifiers", {}).get(state["difficulty"], {})

    opening_messages = []
    for npc_id, npc_config in state["scenario_config"].get("npcs", {}).items():
        diff_messages = npc_config.get("opening_messages", {}).get(state["difficulty"], {})
        if diff_messages:
            for msg in diff_messages.get("messages", []):
                opening_messages.append({
                    "npc_id": npc_id,
                    "npc_name": npc_config.get("name", npc_id),
                    "channel": diff_messages.get("channel", "developer"),
                    "content": msg["content"],
                    "time_offset_minutes": msg.get("time_offset_minutes", 0),
                })

    sara_config = state["scenario_config"].get("npcs", {}).get("sara_khan", {})
    voice_memo = sara_config.get("voice_memo", {}).get(state["difficulty"]) if sara_config else None

    return {
        "opening_messages": opening_messages,
        "voice_memo": voice_memo,
        "sprint_board": scene_config.get("sprint_board") if diff_mods.get("sprint_capacity_visible") else None,
        "hint": diff_mods.get("hint_text") if diff_mods.get("hint_available") else None,
    }


def pause_session(session_id: str, current_user: dict) -> dict:
    state = sessions_repo.load_session(session_id)
    if not state:
        raise HTTPException(status_code=404, detail="Session not found")
    if state["user_id"] != current_user["user_id"] and current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Not your session")

    state["session_status"] = "paused"
    sessions_repo.save_session(session_id, state)
    return {"status": "paused", "session_id": session_id}


def complete_session(session_id: str, current_user: dict) -> dict:
    state = sessions_repo.load_session(session_id)
    if not state:
        raise HTTPException(status_code=404, detail="Session not found")
    if state["user_id"] != current_user["user_id"] and current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Not your session")

    state["session_status"] = "simulation_complete"
    sessions_repo.save_session(session_id, state)
    return {"status": "simulation_complete", "session_id": session_id}
