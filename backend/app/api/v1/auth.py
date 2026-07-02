from fastapi import APIRouter, HTTPException

from app.db.client import get_supabase
from app.schemas.auth import (
    LogoutRequest,
    RefreshRequest,
    SigninRequest,
    SignupRequest,
    TokenResponse,
)
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


def _require_db() -> None:
    if not get_supabase():
        raise HTTPException(status_code=503, detail="Database not configured")


@router.post("/signup", response_model=TokenResponse)
def signup(req: SignupRequest):
    _require_db()
    return auth_service.signup(req.model_dump())


@router.post("/signin", response_model=TokenResponse)
def signin(req: SigninRequest):
    _require_db()
    return auth_service.signin(req.email, req.password)


@router.post("/refresh", response_model=TokenResponse)
def refresh(req: RefreshRequest):
    _require_db()
    return auth_service.refresh(req.refresh_token)


@router.post("/logout")
def logout(req: LogoutRequest):
    _require_db()
    auth_service.logout(req.refresh_token)
    return {"status": "success"}
