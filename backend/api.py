"""
FastAPI Backend — Career Simulator
Connects LangGraph Simulation Director to HTTP endpoints.
Changes from v1:
  - CORS middleware added (required for Vercel → Render calls)
  - Supabase session persistence (replaces in-memory dict)
  - Supabase auth JWT middleware
  - Scene state stored in DB for resume
"""

import os
import uuid
import json
from typing import Optional

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

# ─── SUPABASE CLIENT ─────────────────────────────────────────────────────────
from supabase import create_client, Client

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

supabase: Optional[Client] = None
if SUPABASE_URL.startswith("https://") and SUPABASE_KEY and not SUPABASE_KEY.startswith("your_"):
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("[API] Supabase connected ✓")
else:
    print("[API] WARNING: SUPABASE_URL or SUPABASE_KEY not set. Running in memory-only mode.")

# ─── IN-MEMORY FALLBACK ───────────────────────────────────────────────────────
# Used when Supabase is not configured (local dev without .env)
_memory_sessions: dict = {}

# ─── DIRECTOR ────────────────────────────────────────────────────────────────
from agents.director import build_director, create_initial_state, SimulationState

app = FastAPI(title="Career Simulator — Director API", version="2.0")

director = build_director()

# ─── CORS ────────────────────────────────────────────────────────────────────
# CRITICAL: without this, Vercel frontend cannot call this backend
ALLOWED_ORIGINS = [
    "http://localhost:3000",                          # local Next.js dev
    "https://careerdnaai.vercel.app",                # production Vercel URL
    os.getenv("FRONTEND_URL", ""),                   # set in Render env vars
]
ALLOWED_ORIGINS = [o for o in ALLOWED_ORIGINS if o]  # remove empty strings

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── AUTH MIDDLEWARE ─────────────────────────────────────────────────────────

async def get_current_user(authorization: Optional[str] = Header(None)) -> dict:
    """
    Validates Supabase JWT from Authorization header.
    Falls back to a test user if Supabase is not configured (dev mode).
    """
    if not supabase:
        # Dev mode — no auth required
        return {"user_id": "dev-user-001", "email": "dev@test.com"}

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    token = authorization.split(" ")[1]
    try:
        user = supabase.auth.get_user(token)
        return {"user_id": user.user.id, "email": user.user.email}
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")


# ─── STATE PERSISTENCE ───────────────────────────────────────────────────────

def save_session(session_id: str, state: SimulationState):
    """Save session state to Supabase or memory fallback."""
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
                # scene_state is JSONB NOT NULL — pass a plain dict, not a JSON string
                "scene_state": {
                    "scores": state["scores"],
                    "decisions_log": state["decisions_log"],
                    "stakeholder_trust": state["stakeholder_trust"],
                    "npc_states": state["npc_states"],
                    "sprint_progress": state["sprint_progress"],
                },
                "sprint_progress": state["sprint_progress"],
                "last_active_at": "now()",
            }).execute()
        except Exception as e:
            print(f"[API] Supabase save error: {e} — falling back to memory")
            _memory_sessions[session_id] = state
    else:
        _memory_sessions[session_id] = state


def load_session(session_id: str) -> Optional[SimulationState]:
    """Load session state from Supabase or memory fallback."""
    if supabase:
        try:
            result = supabase.table("sessions").select("*").eq("id", session_id).single().execute()
            if result.data:
                row = result.data
                # scene_state is JSONB — Supabase returns it as a plain dict, not a string
                scene_state = row.get("scene_state") or {}
                if isinstance(scene_state, str):
                    scene_state = json.loads(scene_state)
                # Reconstruct state from DB row + scene_state blob
                state = create_initial_state(session_id, row["user_id"], row["domain"], row["difficulty"])
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
            print(f"[API] Supabase load error: {e}")

    return _memory_sessions.get(session_id)


# ─── REQUEST / RESPONSE SCHEMAS ──────────────────────────────────────────────

class StartSessionRequest(BaseModel):
    domain: str = "pm"
    difficulty: str = "medium"


class ActionRequest(BaseModel):
    session_id: str
    user_action: str


class OnboardingRequest(BaseModel):
    university: str = ""
    degree: str = ""
    graduation_year: str = ""
    career_interests: list[str] = []
    personality_results: dict = {}
    self_rated_pm: int = 3
    self_rated_sqa: int = 3
    self_rated_data: int = 3
    self_rated_frontend: int = 3
    self_rated_backend: int = 3


# ─── ENDPOINTS ───────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {"status": "Career Simulator API running", "version": "2.0"}


@app.get("/health")
def health():
    return {
        "status": "ok",
        "supabase": "connected" if supabase else "memory-only mode",
        "llm_provider": os.getenv("LLM_PROVIDER", "groq"),
    }


@app.post("/session/start")
def start_session(req: StartSessionRequest, current_user: dict = Depends(get_current_user)):
    """
    Creates a new simulation session.
    Loads scenario config from JSON files.
    """
    session_id = str(uuid.uuid4())
    state = create_initial_state(session_id, current_user["user_id"], req.domain, req.difficulty)
    save_session(session_id, state)

    # Get opening messages for this domain/difficulty from NPC config
    opening_messages = []
    for npc_id, npc_config in state["scenario_config"].get("npcs", {}).items():
        diff_messages = npc_config.get("opening_messages", {}).get(req.difficulty, {})
        if diff_messages:
            for msg in diff_messages.get("messages", []):
                opening_messages.append({
                    "npc_id": npc_id,
                    "npc_name": npc_config.get("name", npc_id),
                    "channel": diff_messages.get("channel", "developer"),
                    "content": msg.get("content", ""),
                    "time_offset_minutes": msg.get("time_offset_minutes", 0),
                })

    # Get voice memo for this difficulty
    voice_memo = None
    sara_config = state["scenario_config"].get("npcs", {}).get("sara_khan", {})
    if sara_config:
        voice_memo = sara_config.get("voice_memo", {}).get(req.difficulty)

    # Get difficulty modifiers (hints visibility etc.)
    scene_config = state["scenario_config"]["scenes"].get("scene_1", {})
    diff_mods = scene_config.get("difficulty_modifiers", {}).get(req.difficulty, {})

    print(f"[API] Session started: {session_id} | {req.domain} | {req.difficulty} | user: {current_user['user_id']}")

    return {
        "session_id": session_id,
        "domain": req.domain,
        "difficulty": req.difficulty,
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


@app.post("/session/action")
def handle_action(req: ActionRequest, current_user: dict = Depends(get_current_user)):
    """
    Processes a student action through the LangGraph director.
    Returns structured DirectorResponse to frontend.
    """
    state = load_session(req.session_id)
    if not state:
        raise HTTPException(status_code=404, detail="Session not found")

    # Verify session belongs to this user
    if state["user_id"] != current_user["user_id"] and current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Not your session")

    # Inject action and run director
    state["user_action"] = req.user_action
    updated_state = director.invoke(state)

    # Persist updated state
    save_session(req.session_id, updated_state)

    return {
        "session_id": req.session_id,
        "action_type": updated_state["action_type"],
        "npc_response": updated_state.get("npc_response"),
        "npc_name": "Sara Khan",
        "score_update": updated_state.get("score_update"),
        "next_scene_id": updated_state.get("next_scene_id"),
        "session_status": updated_state["session_status"],
        "ui_events": updated_state.get("ui_events", []),
        "stakeholder_trust": updated_state["stakeholder_trust"],
        "current_scores": updated_state["scores"],
    }


@app.get("/session/{session_id}/state")
def get_state(session_id: str, current_user: dict = Depends(get_current_user)):
    """Returns full session state. Used for resume and admin view."""
    state = load_session(session_id)
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


@app.get("/session/{session_id}/opening")
def get_opening_messages(session_id: str, current_user: dict = Depends(get_current_user)):
    """
    Returns the opening messages and voice memo for a session.
    Called by frontend when simulation loads to populate initial chat.
    """
    state = load_session(session_id)
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


@app.post("/session/{session_id}/pause")
def pause_session(session_id: str, current_user: dict = Depends(get_current_user)):
    """Pauses the session for Save & Exit."""
    state = load_session(session_id)
    if not state:
        raise HTTPException(status_code=404, detail="Session not found")
    if state["user_id"] != current_user["user_id"] and current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Not your session")
    
    state["session_status"] = "paused"
    save_session(session_id, state)
    return {"status": "paused", "session_id": session_id}


@app.post("/session/{session_id}/complete")
def complete_session(session_id: str, current_user: dict = Depends(get_current_user)):
    """Manually completes the session."""
    state = load_session(session_id)
    if not state:
        raise HTTPException(status_code=404, detail="Session not found")
    if state["user_id"] != current_user["user_id"] and current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Not your session")
    
    state["session_status"] = "simulation_complete"
    save_session(session_id, state)
    
    # Ideally trigger report agent here or mark for evaluation
    return {"status": "simulation_complete", "session_id": session_id}


@app.get("/sessions/incomplete")
def get_incomplete_sessions(current_user: dict = Depends(get_current_user)):
    """Returns all active or paused sessions for the user."""
    if not supabase:
        # Memory mode mock
        res = []
        for sid, state in _memory_sessions.items():
            if state["user_id"] == current_user["user_id"] and state["session_status"] in ["active", "paused"]:
                res.append({"session_id": sid, "domain": state["domain"], "status": state["session_status"]})
        return res

    try:
        result = supabase.table("sessions").select("id, domain, difficulty, status, current_scene_id, started_at, last_active_at").eq("user_id", current_user["user_id"]).in_("status", ["active", "paused"]).execute()
        return result.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/user/onboarding")
def save_onboarding_data(req: OnboardingRequest, current_user: dict = Depends(get_current_user)):
    """Saves user onboarding data (personality, knowledge assessment)."""
    if not supabase:
        return {"status": "success (mocked)", "data": req.model_dump()}

    try:
        # Update users table with basic info
        supabase.table("users").update({
            "university": req.university
        }).eq("id", current_user["user_id"]).execute()

        # Upsert user_profiles
        profile_data = {
            "user_id": current_user["user_id"],
            "personality_results": req.personality_results,
            "interest_results": req.career_interests,
            "self_rated_pm": req.self_rated_pm,
            "self_rated_sqa": req.self_rated_sqa,
            "self_rated_data": req.self_rated_data,
            "self_rated_frontend": req.self_rated_frontend,
            "self_rated_backend": req.self_rated_backend,
        }
        supabase.table("user_profiles").upsert(profile_data).execute()
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── REPORT GENERATION ────────────────────────────────────────────────────────

from typing import List as TypingList

class ReportRequest(BaseModel):
    session_ids: TypingList[str]


@app.post("/report/generate")
def generate_report(
    req: ReportRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Generate Career DNA Report for a user based on completed session IDs.
    Calls career_fit_agent then report_agent in sequence.
    """
    from agents.career_fit_agent import generate_fit_report_data
    from agents.report_agent import generate_report_narrative, save_report_to_supabase

    if not req.session_ids:
        raise HTTPException(status_code=400, detail="No session IDs provided")

    sessions_data = []
    for sid in req.session_ids:
        state = load_session(sid)
        if state and state.get("scores"):
            sessions_data.append({
                "domain":        state["domain"],
                "scores":        state["scores"],
                "decisions_log": state["decisions_log"],
                "session_id":    sid
            })

    if not sessions_data:
        raise HTTPException(
            status_code=404,
            detail="No valid completed sessions found for provided IDs"
        )

    fit_data = generate_fit_report_data(current_user["user_id"], sessions_data)
    fit_data["sessions_included"] = req.session_ids

    report = generate_report_narrative(fit_data)

    report_id = None
    if supabase:
        report_id = save_report_to_supabase(report, supabase)

    return {
        "report_id":      report_id,
        "report":         report,
        "fit_scores":     fit_data["domain_fit_scores"],
        "ranked_domains": fit_data["ranked_domains"],
        "confidence":     fit_data["confidence_level"]
    }
