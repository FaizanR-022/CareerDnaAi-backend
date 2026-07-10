"""
Test Suite — repositories, e2e against real Supabase
Exercises the real repository code (not a fake client) against the live
Supabase project configured in .env, via the e2e_user fixture (conftest.py) —
a real, disposable test user whose teardown cascades to clean up everything
created against it during a test.

Run: pytest tests/test_repositories.py
"""
import uuid

import pytest

from app.repositories import auth as auth_repo
from app.repositories import career_dna_reports, npc_state, scene_evaluations
from app.repositories import simulation_scenes, simulation_sessions, user_profile
from app.repositories import users as users_repo
from app.repositories import execute_or_503


# ─── repositories/__init__.py — no DB needed for this one ─────────────────

def test_execute_or_503_passes_through_success():
    class FakeQuery:
        def execute(self):
            return "ok"

    assert execute_or_503(FakeQuery()) == "ok"


def test_execute_or_503_converts_exception_to_503():
    from fastapi import HTTPException

    class FailingQuery:
        def execute(self):
            raise RuntimeError("connection reset")

    with pytest.raises(HTTPException) as exc_info:
        execute_or_503(FailingQuery())
    assert exc_info.value.status_code == 503


# ─── repositories/auth.py ───────────────────────────────────────────────

def test_get_or_create_lookup_creates_and_reuses():
    name = f"Test University {uuid.uuid4().hex[:8]}"
    id1 = auth_repo.get_or_create_lookup("universities", name)
    id2 = auth_repo.get_or_create_lookup("universities", name)
    assert id1 == id2


def test_get_or_create_lookup_blank_name_returns_none():
    assert auth_repo.get_or_create_lookup("universities", "") is None
    assert auth_repo.get_or_create_lookup("universities", "   ") is None


def test_get_user_by_email_and_id_flatten_correctly(e2e_user):
    user = e2e_user["user"]
    by_email = auth_repo.get_user_by_email(user["email"])
    by_id = auth_repo.get_user_by_id(user["id"])

    assert by_email["id"] == user["id"]
    assert by_id["email"] == user["email"]
    assert "university" in by_id  # flattened from the nested FK join
    assert "degree" in by_id


def test_get_user_by_email_missing_returns_none():
    assert auth_repo.get_user_by_email("definitely-not-a-real-user@example.com") is None


def test_refresh_token_lifecycle(e2e_user):
    user = e2e_user["user"]
    token_hash = f"hash-{uuid.uuid4().hex}"
    token_id = auth_repo.save_refresh_token(user["id"], token_hash, "2030-01-01T00:00:00+00:00")

    fetched = auth_repo.get_refresh_token_by_hash(token_hash)
    assert fetched["id"] == token_id
    assert fetched["revoked_at"] is None

    auth_repo.revoke_refresh_token(token_id)
    assert auth_repo.get_refresh_token_by_hash(token_hash)["revoked_at"] is not None


def test_revoke_all_user_tokens(e2e_user):
    user = e2e_user["user"]
    hash_a, hash_b = f"hash-a-{uuid.uuid4().hex}", f"hash-b-{uuid.uuid4().hex}"
    auth_repo.save_refresh_token(user["id"], hash_a, "2030-01-01T00:00:00+00:00")
    auth_repo.save_refresh_token(user["id"], hash_b, "2030-01-01T00:00:00+00:00")

    auth_repo.revoke_all_user_tokens(user["id"])

    assert auth_repo.get_refresh_token_by_hash(hash_a)["revoked_at"] is not None
    assert auth_repo.get_refresh_token_by_hash(hash_b)["revoked_at"] is not None


# ─── repositories/users.py ───────────────────────────────────────────────

def test_update_user_updates_fields(e2e_user):
    user = e2e_user["user"]
    updated = users_repo.update_user(user["id"], {
        "full_name": "Updated Name",
        "university": f"New Uni {uuid.uuid4().hex[:8]}",
        "degree": None,
        "graduation_year": None,
        "core_interests": None,
    })
    assert updated["full_name"] == "Updated Name"
    assert updated["university"]


def test_update_user_raises_for_missing_user():
    with pytest.raises(ValueError):
        users_repo.update_user("00000000-0000-0000-0000-000000000000", {"full_name": "X"})


def test_deactivate_user(e2e_user):
    user = e2e_user["user"]
    users_repo.deactivate_user(user["id"])
    assert auth_repo.get_user_by_id(user["id"])["is_active"] is False


def test_save_onboarding_persists_profile(e2e_user):
    user = e2e_user["user"]
    users_repo.save_onboarding(user["id"], {
        "university": f"Onboard Uni {uuid.uuid4().hex[:8]}",
        "personality_results": {"trait": "high"},
        "career_interests": ["ml"],
    })
    # self_rated_* is DB-defaulted to 3, not collected at onboarding anymore
    assert user_profile.get_self_rating(user["id"], "product_manager") == 3


# ─── new-flow repositories, against real Supabase (not memory mode) ──────

def test_simulation_sessions_e2e(e2e_user):
    user_id = e2e_user["user"]["id"]
    session_id = str(uuid.uuid4())
    row = simulation_sessions.create_session(session_id, user_id, "product_manager", "medium")
    assert row["status"] == "in_progress"

    fetched = simulation_sessions.get_session(session_id)
    assert fetched["user_id"] == user_id

    simulation_sessions.bump_scene_number(session_id, 2)
    assert simulation_sessions.get_session(session_id)["current_scene_number"] == 2

    simulation_sessions.update_status(session_id, "completed")
    assert simulation_sessions.get_session(session_id)["status"] == "completed"

    mine = simulation_sessions.list_sessions_for_user(user_id)
    assert any(s["id"] == session_id for s in mine)


def test_simulation_scenes_and_evaluations_e2e(e2e_user):
    user_id = e2e_user["user"]["id"]
    session_id = str(uuid.uuid4())
    simulation_sessions.create_session(session_id, user_id, "product_manager", "medium")

    scene_id = str(uuid.uuid4())
    simulation_scenes.save_scene(scene_id, session_id, 1, {"title": "Scene one", "narrative": "..."})

    assert simulation_scenes.get_scene(session_id, 1)["id"] == scene_id
    assert simulation_scenes.get_latest_scene(session_id)["scene_number"] == 1
    assert len(simulation_scenes.list_scenes(session_id)) == 1

    eval_id = str(uuid.uuid4())
    scene_evaluations.create_pending(eval_id, scene_id, {"raw_text": "my response"})
    assert scene_evaluations.get_evaluation(scene_id)["evaluated_at"] is None

    saved = scene_evaluations.save_evaluation(scene_id, {
        "overall_score": 88.0,
        "dimension_scores": {"analytical_reasoning": 88.0, "decisiveness": 70.0},
        "behavioral_flags": ["clarification_sought"],
        "justification": "solid reasoning",
    })
    assert saved["overall_score"] == 88.0
    assert saved["decisiveness"] == 70.0

    evals = scene_evaluations.list_evaluations_for_scenes([scene_id])
    assert len(evals) == 1 and evals[0]["evaluated_at"] is not None


def test_npc_state_e2e(e2e_user):
    user_id = e2e_user["user"]["id"]
    session_id = str(uuid.uuid4())
    simulation_sessions.create_session(session_id, user_id, "product_manager", "medium")

    npc_state.apply_npc_state_updates(session_id, [
        {"npc_id": "sara", "trust_score": 65, "sentiment": "positive", "memory_summary": "trusts you now"}
    ])
    trust = npc_state.get_trust(session_id)
    assert len(trust) == 1 and trust[0]["trust_score"] == 65
    assert len(npc_state.get_memory(session_id)) == 1

    # a second update for the same npc_id upserts, doesn't duplicate
    npc_state.apply_npc_state_updates(session_id, [
        {"npc_id": "sara", "trust_score": 80, "sentiment": "positive", "memory_summary": "even more trust"}
    ])
    trust_after = npc_state.get_trust(session_id)
    assert len(trust_after) == 1 and trust_after[0]["trust_score"] == 80


def test_career_dna_reports_e2e(e2e_user):
    user_id = e2e_user["user"]["id"]
    report_id = str(uuid.uuid4())
    career_dna_reports.save_report({
        "id": report_id,
        "user_id": user_id,
        "summary_narrative": "Great potential in product management.",
        "version": 1,
    })

    fetched = career_dna_reports.get_report(report_id)
    assert fetched["user_id"] == user_id

    mine = career_dna_reports.list_reports_for_user(user_id)
    assert any(r["id"] == report_id for r in mine)


def test_user_profile_self_rating_e2e(e2e_user):
    user_id = e2e_user["user"]["id"]
    # no profile row exists until onboarding runs
    assert user_profile.get_self_rating(user_id, "product_manager") is None

    users_repo.save_onboarding(user_id, {
        "university": "", "personality_results": {}, "career_interests": [],
    })
    assert user_profile.get_self_rating(user_id, "product_manager") == 3
