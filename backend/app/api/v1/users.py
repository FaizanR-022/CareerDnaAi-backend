from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import get_current_user, verify_self_or_admin
from app.db.client import get_supabase
from app.repositories import users as users_repo
from app.schemas.auth import UserResponse
from app.schemas.user import OnboardingRequest
from app.services import auth_service

router = APIRouter(tags=["users"])


@router.post("/user/onboarding")
def save_onboarding(req: OnboardingRequest, current_user: dict = Depends(get_current_user)):
    if not get_supabase():
        return {"status": "success (mocked)", "data": req.model_dump()}

    try:
        users_repo.save_onboarding(current_user["user_id"], req.model_dump())
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# NOTE: /users/me must be registered before /users/{user_id} — FastAPI matches
# routes in registration order, and {user_id} would otherwise swallow "me".
@router.get("/users/me", response_model=UserResponse)
def get_my_profile(current_user: dict = Depends(get_current_user)):
    return auth_service.get_user_profile(current_user["user_id"])


@router.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: str, current_user: dict = Depends(get_current_user)):
    verify_self_or_admin(user_id, current_user)
    return auth_service.get_user_profile(user_id)
