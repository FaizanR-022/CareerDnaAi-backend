import asyncio
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
        user_response = eval_row.get("user_response", {}) or {}
        raw_text = user_response.get("raw_text")
        history.append(
            HistoryEntry(
                scene=SceneContent(**scene_row["content"]),
                evaluation=EvaluationResult(**eval_row["evaluation"]),
                student_response=raw_text
            )
        )
    return history


def _prepare_start(session_id: str, user_id: str, domain: Domain, difficulty: Difficulty) -> SceneGenerationContext:
    simulation_sessions.create_session(session_id, user_id, domain, difficulty)
    return SceneGenerationContext(
        simulation_session_id=session_id,
        user_id=user_id,
        domain=domain,
        difficulty=difficulty,
        scene_number=1,
        user_profile_snippet=_get_profile_snippet(user_id, domain),
    )

async def start_simulation(current_user: dict, domain: Domain, difficulty: Difficulty) -> dict:
    user_id = current_user["user_id"]
    session_id = str(uuid.uuid4())
    
    ctx = await asyncio.to_thread(_prepare_start, session_id, user_id, domain, difficulty)
    scene = await agent_client.generate_scene(ctx)
    await asyncio.to_thread(simulation_scenes.save_scene, str(uuid.uuid4()), session_id, 1, scene.model_dump())

    return {"session_id": session_id, "scene": scene.model_dump()}


def _prepare_submit(session_id: str, current_user: dict, scene_number: int, user_response: SubmittedResponse):
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
    return EvaluationContext(
        simulation_session_id=session_id,
        user_id=session["user_id"],
        domain=session["domain"],
        difficulty=session["difficulty"],
        scene_number=scene_number,
        scene_content=scene_content,
        user_response=user_response,
        history=_build_history(session_id),
    ), session, scene_content, scene_id

def _finalize_submit(session_id: str, scene_id: str, result: EvaluationResult, scene_content: SceneContent, session: dict, scene_number: int) -> dict:
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

async def send_message(
    session_id: str,
    scene_number: int,
    student_message: str,
    user: dict
) -> dict:
    """
    Handles a single chat message from student.
    Gets NPC reply. Stores both in conversation_history.
    Does NOT evaluate or advance scene.
    """
    import asyncio
    from app.agents.graph import get_graph
    
    # Verify session ownership
    session = await asyncio.to_thread(
        simulation_sessions.get_session, session_id
    )
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session["user_id"] != user["user_id"]:
        raise HTTPException(status_code=403, detail="Not your session")
    
    # Get current graph state from checkpointer
    config = {"configurable": {"thread_id": session_id}}
    
    async with get_graph() as graph:
        try:
            existing = await graph.aget_state(config)
            if not existing or not existing.values:
                raise HTTPException(status_code=409, detail="No active scene — start simulation first")
        except Exception as e:
            raise HTTPException(status_code=409, detail=f"Cannot retrieve session state: {e}")
        
        current_state = existing.values
        
        # Update state with student message and run npc_reply_node directly
        from app.agents.nodes.npc_reply import npc_reply_node
        
        updated_state = dict(current_state)
        history = current_state.get("conversation_history", [])
        
        # Add system message if scene 2 and empty history
        if scene_number == 2 and len(history) == 0:
            import datetime
            system_msg = {
                "role": "system",
                "content": "Rayan Ahmed (Engineering Lead) has joined the conversation.",
                "timestamp": datetime.datetime.utcnow().isoformat()
            }
            history = list(history) + [system_msg]
            updated_state["conversation_history"] = history
            
        updated_state["student_message"] = student_message
        
        npc_result = await npc_reply_node(updated_state)
        
        # Persist updated conversation_history back to graph state
        await graph.aupdate_state(
            config,
            {
                "conversation_history": npc_result["conversation_history"],
                "npc_reply": npc_result["npc_reply"],
                "active_npc_id": npc_result["active_npc_id"],
            }
        )
    
    # Also persist to Supabase npc_memory table for resume
    active_npc_id = npc_result["active_npc_id"]
    await asyncio.to_thread(
        npc_state_repo.upsert_npc_memory,
        session_id,
        active_npc_id,
        f"Last message: {student_message[:100]}",
    )
    
    domain = current_state.get("domain", "product_manager")
    scene_active_npcs = current_state.get("current_scene", {}).get("context_data", {}).get("active_npcs", [])
    
    def _get_npc_display_name(npc_id: str, domain: str) -> str:
        names = {
            "sara_khan": "Sara Khan",
            "rayan_eng_lead": "Rayan Ahmed",
            "zara_malik": "Zara Malik",
            "dan_frontend_dev": "Dan",
            "vp_analytics": "Jordan",
            "fe_client": "Alex",
            "be_team_lead": "Marcus",
        }
        return names.get(npc_id, npc_id)
    
    return {
        "npc_id": active_npc_id,
        "npc_name": _get_npc_name(npc_result["conversation_history"]),
        "content": npc_result["npc_reply"],
        "conversation_history": npc_result["conversation_history"],
        "all_active_npcs": [
            {
                "npc_id": npc_id,
                "npc_name": _get_npc_display_name(npc_id, domain),
                "can_receive_messages": True
            }
            for npc_id in scene_active_npcs
        ],
        "is_multi_npc": len(scene_active_npcs) > 1
    }

def _get_npc_name(history: list) -> str:
    """Extract NPC name from last NPC message in history."""
    for msg in reversed(history):
        if msg["role"] == "npc":
            return msg.get("npc_name", "NPC")
    return "NPC"


def _evaluate_da_submission(scene_number: int, user_response: SubmittedResponse) -> dict:
    validation = {"is_valid": False, "errors": []}
    structured = user_response.structured or {}
    
    if scene_number == 1:
        if structured.get("imputation_strategy") == "impute_mean" and structured.get("duplicate_handling") == "keep_first":
            validation["is_valid"] = True
        else:
            validation["errors"].append("Incorrect pipeline configuration. Expected impute_mean and keep_first.")
            
    elif scene_number == 2:
        query = (structured.get("query") or "").lower()
        required = ["select", "from", "transaction_log", "timestamp", "volume"]
        missing = [kw for kw in required if kw not in query]
        if not missing:
            validation["is_valid"] = True
        else:
            validation["errors"].append(f"SQL missing required keywords: {', '.join(missing)}")
            
    elif scene_number == 3:
        code = (structured.get("code") or "").replace(" ", "").replace('"', "'")
        if "df.plot" in code and "x='timestamp'" in code and "y='volume'" in code:
            validation["is_valid"] = True
        else:
            validation["errors"].append("Python code missing df.plot with x='timestamp' and y='volume'.")
            
    elif scene_number == 4:
        hyp = structured.get("hypothesis_id")
        text = structured.get("text_analysis") or ""
        if hyp == "hyp_divergence" and len(text) >= 30:
            validation["is_valid"] = True
        else:
            if hyp != "hyp_divergence":
                validation["errors"].append("Incorrect hypothesis selected.")
            if len(text) < 30:
                validation["errors"].append("Text analysis is too short (must be >= 30 chars).")
                
    return validation


async def submit_response(
    session_id: str,
    current_user: dict,
    scene_number: int,
    user_response: SubmittedResponse,
) -> dict:
    from app.agents.graph import get_graph
    config = {"configurable": {"thread_id": session_id}}
    
    async with get_graph() as graph:
        existing = await graph.aget_state(config)
        
        state = existing.values if existing else {}
        conv_history = state.get("conversation_history", [])
        all_student_messages = " | ".join([
            msg["content"] for msg in conv_history 
            if msg["role"] == "student"
        ])
        
        # Use combined messages if available, otherwise use what was submitted
        user_response.raw_text = all_student_messages or (user_response.raw_text or "")
    
        eval_ctx, session, scene_content, scene_id = await asyncio.to_thread(_prepare_submit, session_id, current_user, scene_number, user_response)
        
        if session["domain"] == "data_analyst":
            validation = _evaluate_da_submission(scene_number, user_response)
            await graph.aupdate_state(config, {"da_validation_status": validation})
            # Pass validation to LLM evaluator
            user_response.raw_text = (user_response.raw_text or "") + f"\n\n[Backend DA Validation]: {validation}"
    
    result = await agent_client.evaluate_response(eval_ctx)
    return await asyncio.to_thread(_finalize_submit, session_id, scene_id, result, scene_content, session, scene_number)


def _prepare_next(session_id: str, current_user: dict):
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
    return SceneGenerationContext(
        simulation_session_id=session_id,
        user_id=session["user_id"],
        domain=session["domain"],
        difficulty=session["difficulty"],
        scene_number=next_number,
        user_profile_snippet=_get_profile_snippet(session["user_id"], session["domain"]),
        history=_build_history(session_id),
    ), next_number

def _finalize_next(session_id: str, next_number: int, scene: SceneContent):
    simulation_scenes.save_scene(str(uuid.uuid4()), session_id, next_number, scene.model_dump())
    simulation_sessions.bump_scene_number(session_id, next_number)

async def request_next_scene(session_id: str, current_user: dict) -> dict:
    ctx, next_number = await asyncio.to_thread(_prepare_next, session_id, current_user)
    scene = await agent_client.generate_scene(ctx)
    await asyncio.to_thread(_finalize_next, session_id, next_number, scene)
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
