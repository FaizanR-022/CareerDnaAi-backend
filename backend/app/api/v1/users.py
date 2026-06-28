from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import get_current_user
from app.db.client import get_supabase
from app.repositories import users as users_repo
from app.schemas.user import OnboardingRequest

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
