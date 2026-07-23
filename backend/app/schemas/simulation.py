from typing import Literal

from pydantic import BaseModel

from app.schemas.agent_contracts import (
    Difficulty,
    Domain,
    EvaluationResult,
    SceneContent,
    SubmittedResponse,
)

SimulationStatus = Literal["in_progress", "completed", "abandoned"]


# ─── Requests ─────────────────────────────────────────────────────────────

class StartSimulationRequest(BaseModel):
    domain: Domain
    difficulty: Difficulty = "medium"


class SubmitResponseRequest(BaseModel):
    """scene_number comes from the URL path
    (POST /simulations/{id}/scenes/{scene_number}/responses), not the body."""

    response: SubmittedResponse


class SendMessageRequest(BaseModel):
    """Request body for POST /simulations/{id}/scenes/{n}/messages"""
    message: str  # the student's message text
    channel: str | None = None  # The UI channel (NPC name) the student is talking in


class NPCReplyResponse(BaseModel):
    """Response for the NPC chat endpoint"""
    npc_id: str
    npc_name: str
    content: str
    conversation_history: list  # full history so far in this scene


# ─── Responses ────────────────────────────────────────────────────────────

class SceneResponse(BaseModel):
    """Shared shape for /start, /next-scene, /current-scene."""

    session_id: str
    scene: SceneContent


class SubmitResponseResponse(BaseModel):
    session_id: str
    scene_number: int
    evaluation: EvaluationResult
    is_final_scene: bool
    session_status: SimulationStatus


class SceneProgress(BaseModel):
    scene_number: int
    generated: bool
    evaluated: bool
    overall_score: float | None = None


class SimulationStateResponse(BaseModel):
    session_id: str
    status: SimulationStatus
    current_scene_number: int
    scenes: list[SceneProgress]


class SimulationSessionSummary(BaseModel):
    id: str
    user_id: str
    domain: Domain
    difficulty: Difficulty
    status: SimulationStatus
    current_scene_number: int
    started_at: str
    completed_at: str | None = None
    last_active_at: str
