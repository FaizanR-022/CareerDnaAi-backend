import os

with open("app/api/v1/users.py", "r") as f:
    content = f.read()

# Add the /users/me delete route
delete_me_route = """
@router.delete("/users/me")
def delete_my_profile(current_user: dict = Depends(get_current_user)):
    user_id = current_user["user_id"]
    if not get_supabase():
        return {"status": "deactivated (mocked)", "user_id": user_id}
    users_repo.deactivate_user(user_id)
    auth_repo.revoke_all_user_tokens(user_id)
    return {"status": "deactivated", "user_id": user_id}


@router.get("/users/{user_id}", response_model=UserResponse)
"""

content = content.replace('@router.get("/users/{user_id}", response_model=UserResponse)', delete_me_route)

with open("app/api/v1/users.py", "w") as f:
    f.write(content)
