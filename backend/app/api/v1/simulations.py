from fastapi import APIRouter, Depends

from app.core.auth import get_current_user
from app.schemas.simulation import (
    SceneResponse,
    SimulationSessionSummary,
    SimulationStateResponse,
    StartSimulationRequest,
    SubmitResponseRequest,
    SubmitResponseResponse,
    SendMessageRequest,
    NPCReplyResponse,
)
from app.services import simulation_service

router = APIRouter(prefix="/simulations", tags=["simulations"])


@router.post("", response_model=SceneResponse, status_code=201)
async def start_simulation(req: StartSimulationRequest, current_user: dict = Depends(get_current_user)):
    return await simulation_service.start_simulation(current_user, req.domain, req.difficulty)


@router.post(
    "/{session_id}/scenes/{scene_number}/messages",
    summary="Send a message and get NPC reply (no evaluation, no scene advance)"
)
async def send_message(
    session_id: str,
    scene_number: int,
    req: SendMessageRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Student sends a message to the NPC during a scene.
    NPC responds based on their persona and the conversation so far.
    Does NOT evaluate or advance the scene.
    Call /responses when the student is done to evaluate everything.
    """
    return await simulation_service.send_message(
        session_id=session_id,
        scene_number=scene_number,
        student_message=req.message,
        user=current_user,
        channel=req.channel
    )


@router.post("/{session_id}/scenes/{scene_number}/responses", response_model=SubmitResponseResponse)
async def submit_response(
    session_id: str,
    scene_number: int,
    req: SubmitResponseRequest,
    current_user: dict = Depends(get_current_user),
):
    return await simulation_service.submit_response(
        session_id, current_user, scene_number, req.response
    )


@router.post("/{session_id}/scenes", response_model=SceneResponse)
async def next_scene(session_id: str, current_user: dict = Depends(get_current_user)):
    return await simulation_service.request_next_scene(session_id, current_user)


@router.get("/{session_id}/scenes/current", response_model=SceneResponse)
def current_scene(session_id: str, current_user: dict = Depends(get_current_user)):
    return simulation_service.get_current_scene(session_id, current_user)


@router.get("/{session_id}", response_model=SimulationStateResponse)
def get_simulation(session_id: str, current_user: dict = Depends(get_current_user)):
    return simulation_service.get_state(session_id, current_user)


@router.get("", response_model=list[SimulationSessionSummary])
def list_simulations(current_user: dict = Depends(get_current_user)):
    return simulation_service.list_mine(current_user)
