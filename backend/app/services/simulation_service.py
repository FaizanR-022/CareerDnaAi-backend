import logging
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException

from app.core.auth import verify_session_ownership
from app.db.client import get_supabase
from app.repositories import auth as auth_repo
from app.repositories import scene_evaluations, simulation_scenes, simulation_sessions
from app.repositories import npc_state as npc_state_repo
from app.repositories import user_profile as user_profile_repo
from app.schemas.agent_contracts import (
    Difficulty,
    Domain,
    EvaluationContext,
    EvaluationResult,
    HistoryEntry,
    SceneContent,
    SceneGenerationContext,
    SubmittedResponse,
    UserProfileSnippet,
)
from app.services import agent_client

logger = logging.getLogger(__name__)


def _get_owned_session(session_id: str, current_user: dict) -> dict:
    session = simulation_sessions.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Simulation session not found")
    verify_session_ownership(session, current_user)
    return session


def _get_profile_snippet(user_id: str, domain: str) -> UserProfileSnippet:
    # auth_repo has no memory-fallback branch (assumes Supabase is always
    # configured) — guard the call ourselves so simulations still start in
    # memory-only dev mode, same degrade-to-empty behavior as get_self_rating.
    core_interests = []
    if get_supabase():
        user = auth_repo.get_user_by_id(user_id)
        core_interests = user.get("core_interests", []) if user else []
    self_rating = user_profile_repo.get_self_rating(user_id, domain)
    return UserProfileSnippet(self_rating=self_rating, core_interests=core_interests)


def _build_history(session_id: str) -> list[HistoryEntry]:
    scenes = simulation_scenes.list_scenes(session_id)
    evaluations = {
        e["scene_id"]: e
        for e in scene_evaluations.list_evaluations_for_scenes([s["id"] for s in scenes])
    }

    history = []
    for scene_row in scenes:
        eval_row = evaluations.get(scene_row["id"])
        if not eval_row or not eval_row.get("evaluation"):
            continue  # not yet evaluated — excluded from history
        history.append(
            HistoryEntry(
                scene=SceneContent(**scene_row["content"]),
                evaluation=EvaluationResult(**eval_row["evaluation"]),
            )
        )
    return history


def start_simulation(current_user: dict, domain: Domain, difficulty: Difficulty) -> dict:
    user_id = current_user["user_id"]
    session_id = str(uuid.uuid4())
    simulation_sessions.create_session(session_id, user_id, domain, difficulty)

    ctx = SceneGenerationContext(
        simulation_session_id=session_id,
        user_id=user_id,
        domain=domain,
        difficulty=difficulty,
        scene_number=1,
        user_profile_snippet=_get_profile_snippet(user_id, domain),
    )
    scene = agent_client.generate_scene(ctx)
    simulation_scenes.save_scene(str(uuid.uuid4()), session_id, 1, scene.model_dump())

    return {"session_id": session_id, "scene": scene.model_dump()}


def submit_response(
    session_id: str,
    current_user: dict,
    scene_number: int,
    user_response: SubmittedResponse,
) -> dict:
    session = _get_owned_session(session_id, current_user)
    if session["status"] == "completed":
        raise HTTPException(status_code=409, detail="Simulation already completed")
    if scene_number != session["current_scene_number"]:
        raise HTTPException(status_code=409, detail="Not the current scene")

    scene_row = simulation_scenes.get_scene(session_id, scene_number)
    if not scene_row:
        raise HTTPException(status_code=404, detail="Scene not found")
    scene_id = scene_row["id"]

    existing_eval = scene_evaluations.get_evaluation(scene_id)
    if existing_eval and existing_eval.get("evaluated_at"):
        raise HTTPException(status_code=409, detail="Scene already evaluated")
    if not existing_eval:
        scene_evaluations.create_pending(str(uuid.uuid4()), scene_id, user_response.model_dump())

    scene_content = SceneContent(**scene_row["content"])
    eval_ctx = EvaluationContext(
        simulation_session_id=session_id,
        user_id=session["user_id"],
        domain=session["domain"],
        difficulty=session["difficulty"],
        scene_number=scene_number,
        scene_content=scene_content,
        user_response=user_response,
        history=_build_history(session_id),
    )
    result = agent_client.evaluate_response(eval_ctx)
    scene_evaluations.save_evaluation(scene_id, result.model_dump())

    if result.npc_state_updates:
        npc_state_repo.apply_npc_state_updates(
            session_id, [u.model_dump() for u in result.npc_state_updates]
        )

    lowered_difficulty = result.extra.get("lowered_difficulty")
    if lowered_difficulty:
        simulation_sessions.update_difficulty(session_id, lowered_difficulty)

    if scene_content.is_final_scene:
        simulation_sessions.update_status(
            session_id, "completed", completed_at=datetime.now(timezone.utc).isoformat()
        )
        session_status = "completed"
    else:
        simulation_sessions.touch_last_active(session_id)
        session_status = session["status"]

    return {
        "session_id": session_id,
        "scene_number": scene_number,
        "evaluation": result.model_dump(),
        "is_final_scene": scene_content.is_final_scene,
        "session_status": session_status,
    }


def request_next_scene(session_id: str, current_user: dict) -> dict:
    session = _get_owned_session(session_id, current_user)
    if session["status"] == "completed":
        raise HTTPException(status_code=409, detail="Simulation already completed")

    current_number = session["current_scene_number"]
    current_scene_row = simulation_scenes.get_scene(session_id, current_number)
    if not current_scene_row:
        raise HTTPException(status_code=404, detail="Current scene not found")

    current_eval = scene_evaluations.get_evaluation(current_scene_row["id"])
    if not current_eval or not current_eval.get("evaluated_at"):
        raise HTTPException(status_code=409, detail="Current scene not yet evaluated")

    next_number = current_number + 1
    ctx = SceneGenerationContext(
        simulation_session_id=session_id,
        user_id=session["user_id"],
        domain=session["domain"],
        difficulty=session["difficulty"],
        scene_number=next_number,
        user_profile_snippet=_get_profile_snippet(session["user_id"], session["domain"]),
        history=_build_history(session_id),
    )
    scene = agent_client.generate_scene(ctx)
    simulation_scenes.save_scene(str(uuid.uuid4()), session_id, next_number, scene.model_dump())
    simulation_sessions.bump_scene_number(session_id, next_number)

    return {"session_id": session_id, "scene": scene.model_dump()}


def get_current_scene(session_id: str, current_user: dict) -> dict:
    session = _get_owned_session(session_id, current_user)
    scene_row = simulation_scenes.get_scene(session_id, session["current_scene_number"])
    if not scene_row:
        raise HTTPException(status_code=404, detail="Scene not found")
    return {"session_id": session_id, "scene": scene_row["content"]}


def get_state(session_id: str, current_user: dict) -> dict:
    session = _get_owned_session(session_id, current_user)
    scenes = simulation_scenes.list_scenes(session_id)
    evaluations = {
        e["scene_id"]: e
        for e in scene_evaluations.list_evaluations_for_scenes([s["id"] for s in scenes])
    }

    scene_progress = []
    for scene_row in scenes:
        eval_row = evaluations.get(scene_row["id"])
        scene_progress.append({
            "scene_number": scene_row["scene_number"],
            "generated": True,
            "evaluated": bool(eval_row and eval_row.get("evaluated_at")),
            "overall_score": eval_row.get("overall_score") if eval_row else None,
        })

    return {
        "session_id": session_id,
        "status": session["status"],
        "current_scene_number": session["current_scene_number"],
        "scenes": scene_progress,
    }


def list_mine(current_user: dict) -> list[dict]:
    return simulation_sessions.list_sessions_for_user(current_user["user_id"])
