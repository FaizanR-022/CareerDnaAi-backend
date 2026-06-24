"""
NOTE: THIS IS ONLY SCAFFOLDING AND IS MISSING A LOT.
NEED TO ADD: REAL AGENT LOGIC, DATABASE, GROQ INTEGRATION, SCENARIO FILES, SCORING ENGINE, CAREER DNA ENGINE, NPC MEMORY

FastAPI Integration Layer
Connects the LangGraph Simulation Director to HTTP endpoints.
The frontend calls POST /session/action for every student action.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from agents.director import build_director, create_initial_state, SimulationState

app = FastAPI(title="Career Simulator — Simulation Director API")

# Compile the graph once at startup — reuse for all requests
director = build_director()

# In-memory session store (replace with Postgres in production)
sessions: dict[str, SimulationState] = {}


class ActionRequest(BaseModel):
    session_id: str
    user_action: str


class StartSessionRequest(BaseModel):
    user_id: str
    domain: str = "pm"
    difficulty: str = "medium"


@app.post("/session/start")
def start_session(req: StartSessionRequest):
    """Creates a new simulation session and returns the session_id."""
    import uuid
    session_id = str(uuid.uuid4())
    state = create_initial_state(session_id, req.user_id, req.domain, req.difficulty)
    sessions[session_id] = state
    return {
        "session_id": session_id,
        "current_scene_id": state["current_scene_id"],
        "scene_context": state["scenario_config"]["scenes"]["scene_1"]["context"],
        "status": "started",
    }


@app.post("/session/action")
def handle_action(req: ActionRequest):
    """
    Main endpoint. Called on every student action.
    Runs the full LangGraph director cycle and returns structured response.
    """
    if req.session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    # Load current state, inject user action
    state = sessions[req.session_id]
    state["user_action"] = req.user_action

    # Run director graph
    updated_state = director.invoke(state)

    # Persist updated state (write to Postgres in production)
    sessions[req.session_id] = updated_state

    # Return structured response to frontend
    return {
        "session_id": req.session_id,
        "action_type": updated_state["action_type"],
        "npc_response": updated_state.get("npc_response"),
        "score_update": updated_state.get("score_update"),
        "next_scene_id": updated_state.get("next_scene_id"),
        "session_status": updated_state["session_status"],
        "ui_events": updated_state.get("ui_events", []),
        "stakeholder_trust": updated_state["stakeholder_trust"],
        "current_scores": updated_state["scores"],
    }


@app.get("/session/{session_id}/state")
def get_state(session_id: str):
    """Returns full session state. Used for debug/admin view and frontend resume."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    state = sessions[session_id]
    return {
        "session_id": session_id,
        "current_scene_id": state["current_scene_id"],
        "session_status": state["session_status"],
        "scores": state["scores"],
        "decisions_log": state["decisions_log"],
        "stakeholder_trust": state["stakeholder_trust"],
        "scenes_completed": state["scenes_completed"],
    }
