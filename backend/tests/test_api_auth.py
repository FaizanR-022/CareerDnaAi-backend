"""
Test Suite — /api/v1/auth/* at the real HTTP layer
Previously only ever tested at the service layer (test_auth.py) or verified
manually. This hits the actual routes via TestClient, against real Supabase.

Run: pytest tests/test_api_auth.py
"""
import uuid

from app.db.client import get_supabase


def _signup_payload():
    return {
        "full_name": "API Test User",
        "email": f"pytest-api-{uuid.uuid4().hex[:12]}@example.com",
        "password": "a-long-enough-password",
    }


def test_signup_returns_201_and_envelope(api_client):
    if not get_supabase():
        import pytest
        pytest.skip("Supabase not configured")

    payload = _signup_payload()
    r = api_client.post("/api/v1/auth/signup", json=payload)
    assert r.status_code == 201
    body = r.json()
    assert body["success"] is True
    assert body["data"]["user"]["email"] == payload["email"].lower()
    assert body["data"]["access_token"]

    get_supabase().table("users").delete().eq("id", body["data"]["user"]["id"]).execute()


def test_signup_duplicate_email_returns_409(api_client):
    if not get_supabase():
        import pytest
        pytest.skip("Supabase not configured")

    payload = _signup_payload()
    r1 = api_client.post("/api/v1/auth/signup", json=payload)
    assert r1.status_code == 201
    user_id = r1.json()["data"]["user"]["id"]

    r2 = api_client.post("/api/v1/auth/signup", json=payload)
    assert r2.status_code == 409
    assert r2.json()["success"] is False

    get_supabase().table("users").delete().eq("id", user_id).execute()


def test_signup_validation_error_returns_422(api_client):
    r = api_client.post("/api/v1/auth/signup", json={"email": "not-an-email", "password": "x"})
    assert r.status_code == 422
    assert r.json()["success"] is False


def test_signin_and_refresh_and_logout_flow(api_client):
    if not get_supabase():
        import pytest
        pytest.skip("Supabase not configured")

    payload = _signup_payload()
    signup = api_client.post("/api/v1/auth/signup", json=payload)
    user_id = signup.json()["data"]["user"]["id"]

    signin = api_client.post(
        "/api/v1/auth/signin", json={"email": payload["email"], "password": payload["password"]}
    )
    assert signin.status_code == 200
    assert signin.json()["data"]["access_token"]

    old_refresh = signin.json()["data"]["refresh_token"]
    refreshed = api_client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
    assert refreshed.status_code == 200
    new_refresh = refreshed.json()["data"]["refresh_token"]
    assert new_refresh != old_refresh

    logout = api_client.post("/api/v1/auth/logout", json={"refresh_token": new_refresh})
    assert logout.status_code == 200
    assert logout.json()["success"] is True

    get_supabase().table("users").delete().eq("id", user_id).execute()


def test_signin_wrong_password_returns_401(api_client):
    if not get_supabase():
        import pytest
        pytest.skip("Supabase not configured")

    payload = _signup_payload()
    signup = api_client.post("/api/v1/auth/signup", json=payload)
    user_id = signup.json()["data"]["user"]["id"]

    r = api_client.post(
        "/api/v1/auth/signin", json={"email": payload["email"], "password": "wrong-password"}
    )
    assert r.status_code == 401
    assert r.json()["success"] is False

    get_supabase().table("users").delete().eq("id", user_id).execute()
