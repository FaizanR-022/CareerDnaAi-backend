from fastapi import APIRouter, Depends

from app.core.auth import get_current_user
from app.repositories import sessions as sessions_repo
from app.schemas.session import ActionRequest, StartSessionRequest
from app.services import session_service

router = APIRouter(tags=["sessions"])


@router.post("/session/start")
def start_session(req: StartSessionRequest, current_user: dict = Depends(get_current_user)):
    return session_service.start_session(current_user["user_id"], req.domain, req.difficulty)


@router.post("/session/action")
def handle_action(req: ActionRequest, current_user: dict = Depends(get_current_user)):
    return session_service.handle_action(req.session_id, req.user_action, current_user)


@router.get("/session/{session_id}/state")
def get_state(session_id: str, current_user: dict = Depends(get_current_user)):
    return session_service.get_session_state(session_id)


@router.get("/session/{session_id}/opening")
def get_opening(session_id: str, current_user: dict = Depends(get_current_user)):
    return session_service.get_opening_messages(session_id)


@router.post("/session/{session_id}/pause")
def pause_session(session_id: str, current_user: dict = Depends(get_current_user)):
    return session_service.pause_session(session_id, current_user)


@router.post("/session/{session_id}/complete")
def complete_session(session_id: str, current_user: dict = Depends(get_current_user)):
    return session_service.complete_session(session_id, current_user)


@router.get("/sessions/incomplete")
def get_incomplete(current_user: dict = Depends(get_current_user)):
    return sessions_repo.get_incomplete_sessions(current_user["user_id"])
