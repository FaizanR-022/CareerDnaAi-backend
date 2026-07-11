import sys
from pathlib import Path

# Make `app` importable when running pytest from the backend/ directory
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest



# ─── E2E FIXTURES (real Supabase, no mock client) ───────────────────────────
# Project decision: DB-touching tests run against the real Supabase project
# already configured in .env, not a fake/mock client — see conversation. Each
# fixture skips cleanly (not a hard failure) if Supabase isn't reachable, so
# the suite doesn't break on a machine without credentials configured.

import uuid  # noqa: E402

from app.db.client import get_supabase, init_supabase  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _ensure_supabase_connected():
    init_supabase()


@pytest.fixture
def e2e_user():
    """A real, disposable test user created via the actual signup flow (not
    a stand-in). Deletes the user in teardown; ON DELETE CASCADE cleans up
    everything hung off it (sessions, scenes, evaluations, trust, memory,
    reports, refresh_tokens, user_profiles) that a test created."""
    if not get_supabase():
        pytest.skip("Supabase not configured — skipping e2e test")

    from app.services import auth_service

    email = f"pytest-e2e-{uuid.uuid4().hex[:12]}@example.com"
    signup_result = auth_service.signup({
        "email": email,
        "password": "pytest-e2e-password-123",
        "full_name": "Pytest E2E User",
        "university": "",
        "degree": "",
        "graduation_year": None,
        "core_interests": [],
    })

    yield signup_result

    get_supabase().table("users").delete().eq("id", signup_result["user"]["id"]).execute()


@pytest.fixture
def auth_headers(e2e_user):
    return {"Authorization": f"Bearer {e2e_user['access_token']}"}


@pytest.fixture
def api_client():
    from fastapi.testclient import TestClient

    import app.main as main_module

    return TestClient(main_module.app)
