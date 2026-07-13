from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import get_current_user, verify_self_or_admin
from app.db.client import get_supabase
from app.repositories import auth as auth_repo
from app.repositories import users as users_repo
from app.schemas.agent_contracts import MCQGenerationContext, MCQGenerationResult
from app.schemas.auth import UserResponse
from app.schemas.user import OnboardingRequest, UpdateUserRequest
from app.services import agent_client, auth_service

router = APIRouter(tags=["users"])


@router.post("/user/onboarding", response_model=MCQGenerationResult)
async def save_onboarding(req: OnboardingRequest, current_user: dict = Depends(get_current_user)):
    if get_supabase():
        users_repo.save_onboarding(current_user["user_id"], req.model_dump())

    ctx = MCQGenerationContext(
        user_id=current_user["user_id"],
        chosen_field=req.chosen_field,
        self_assessment=req.self_assessment,
    )
    return await agent_client.generate_mcqs(ctx)


# NOTE: /users/me must be registered before /users/{user_id} — FastAPI matches
# routes in registration order, and {user_id} would otherwise swallow "me".
@router.get("/users/me", response_model=UserResponse)
def get_my_profile(current_user: dict = Depends(get_current_user)):
    return auth_service.get_user_profile(current_user["user_id"])


@router.patch("/users/me", response_model=UserResponse)
def update_my_profile(req: UpdateUserRequest, current_user: dict = Depends(get_current_user)):
    if not get_supabase():
        return auth_service.get_user_profile(current_user["user_id"])
    try:
        updated = users_repo.update_user(current_user["user_id"], req.model_dump())
    except ValueError:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "id": updated["id"],
        "email": updated["email"],
        "full_name": updated["full_name"],
        "role": updated["role"],
        "university": updated.get("university") or "",
        "degree": updated.get("degree") or "",
        "graduation_year": updated.get("graduation_year"),
        "core_interests": updated.get("core_interests") or [],
    }


@router.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: str, current_user: dict = Depends(get_current_user)):
    verify_self_or_admin(user_id, current_user)
    return auth_service.get_user_profile(user_id)


@router.delete("/users/{user_id}")
def delete_user(user_id: str, current_user: dict = Depends(get_current_user)):
    verify_self_or_admin(user_id, current_user)
    if not get_supabase():
        return {"status": "deactivated (mocked)", "user_id": user_id}
    users_repo.deactivate_user(user_id)
    auth_repo.revoke_all_user_tokens(user_id)
    return {"status": "deactivated", "user_id": user_id}
