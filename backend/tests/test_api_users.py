"""
Test Suite — /api/v1/users/* and /api/v1/user/onboarding at the real HTTP
layer, against real Supabase. Uses the e2e_user + auth_headers fixtures
(real signup, real JWT bearer auth — not a dependency override).

Run: pytest tests/test_api_users.py
"""


def test_get_my_profile(api_client, e2e_user, auth_headers):
    r = api_client.get("/api/v1/users/me", headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert body["data"]["email"] == e2e_user["user"]["email"]


def test_get_my_profile_requires_auth(api_client):
    r = api_client.get("/api/v1/users/me")
    assert r.status_code == 401
    assert r.json()["success"] is False


def test_onboarding_returns_mcqs(api_client, auth_headers):
    r = api_client.post(
        "/api/v1/user/onboarding",
        headers=auth_headers,
        json={
            "chosen_field": "product_manager",
            "self_assessment": [{"question": "Comfortable with ambiguity?", "score": 4}],
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert len(body["data"]["questions"]) == 5
    for q in body["data"]["questions"]:
        assert len(q["options"]) == 4


def test_onboarding_requires_chosen_field(api_client, auth_headers):
    r = api_client.post("/api/v1/user/onboarding", headers=auth_headers, json={})
    assert r.status_code == 422
    assert r.json()["success"] is False


def test_update_my_profile(api_client, auth_headers):
    r = api_client.patch(
        "/api/v1/users/me", headers=auth_headers, json={"full_name": "Updated Via API"}
    )
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert body["data"]["full_name"] == "Updated Via API"


def test_get_other_users_profile_forbidden(api_client, e2e_user, auth_headers):
    r = api_client.get("/api/v1/users/00000000-0000-0000-0000-000000000000", headers=auth_headers)
    assert r.status_code == 403
    assert r.json()["success"] is False


def test_delete_user_blocks_future_signin(api_client, e2e_user, auth_headers):
    user_id = e2e_user["user"]["id"]
    email = e2e_user["user"]["email"]

    r = api_client.delete(f"/api/v1/users/{user_id}", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["success"] is True

    # signin with the (unknown to us) original password isn't tested here —
    # instead confirm the account is deactivated, which auth_service.signin
    # checks regardless of password correctness (see test_auth.py for the
    # is_active check itself, already covered at the service layer).
    from app.repositories import auth as auth_repo
    assert auth_repo.get_user_by_id(user_id)["is_active"] is False
