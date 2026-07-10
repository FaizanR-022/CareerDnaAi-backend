"""
Test Suite — memory-fallback branch of the new-flow repositories
Since test_repositories.py exercises these against real Supabase (project
decision — no mock client), this file explicitly covers the "Supabase not
configured" code path each repo also has, so it isn't silently untested.

Run: pytest tests/test_memory_fallback.py
"""
import uuid

import pytest

import app.db.client as db_client
from app.repositories import (
    career_dna_reports,
    npc_state,
    scene_evaluations,
    simulation_scenes,
    simulation_sessions,
    user_profile,
)


@pytest.fixture(autouse=True)
def memory_only(monkeypatch):
    monkeypatch.setattr(db_client, "_supabase", None)
    yield


def test_simulation_sessions_memory_fallback():
    session_id = str(uuid.uuid4())
    row = simulation_sessions.create_session(session_id, "user-1", "product_manager", "medium")
    assert row["status"] == "in_progress"

    fetched = simulation_sessions.get_session(session_id)
    assert fetched["id"] == session_id

    simulation_sessions.update_status(session_id, "completed")
    assert simulation_sessions.get_session(session_id)["status"] == "completed"

    simulation_sessions.bump_scene_number(session_id, 2)
    assert simulation_sessions.get_session(session_id)["current_scene_number"] == 2

    mine = simulation_sessions.list_sessions_for_user("user-1")
    assert any(s["id"] == session_id for s in mine)


def test_simulation_scenes_memory_fallback():
    session_id = str(uuid.uuid4())
    scene_id = str(uuid.uuid4())
    simulation_scenes.save_scene(scene_id, session_id, 1, {"title": "test scene"})

    assert simulation_scenes.get_scene(session_id, 1)["id"] == scene_id
    assert simulation_scenes.get_latest_scene(session_id)["scene_number"] == 1
    assert len(simulation_scenes.list_scenes(session_id)) == 1


def test_scene_evaluations_memory_fallback():
    scene_id = str(uuid.uuid4())
    eval_id = str(uuid.uuid4())
    scene_evaluations.create_pending(eval_id, scene_id, {"raw_text": "hello"})
    assert scene_evaluations.get_evaluation(scene_id)["evaluation"] is None

    saved = scene_evaluations.save_evaluation(scene_id, {
        "overall_score": 80.0,
        "dimension_scores": {"analytical_reasoning": 80.0},
        "behavioral_flags": [],
        "justification": "solid",
    })
    assert saved["overall_score"] == 80.0
    assert saved["analytical_reasoning"] == 80.0

    evals = scene_evaluations.list_evaluations_for_scenes([scene_id])
    assert len(evals) == 1


def test_npc_state_memory_fallback():
    session_id = str(uuid.uuid4())
    npc_state.apply_npc_state_updates(session_id, [
        {"npc_id": "npc-1", "trust_score": 60, "sentiment": "positive", "memory_summary": "trusts you"}
    ])

    trust = npc_state.get_trust(session_id)
    assert len(trust) == 1 and trust[0]["trust_score"] == 60

    memory = npc_state.get_memory(session_id)
    assert len(memory) == 1 and memory[0]["memory_summary"] == "trusts you"


def test_npc_state_skips_memory_upsert_when_summary_none():
    session_id = str(uuid.uuid4())
    npc_state.apply_npc_state_updates(session_id, [
        {"npc_id": "npc-1", "trust_score": 60, "sentiment": "positive", "memory_summary": None}
    ])
    assert npc_state.get_trust(session_id)
    assert npc_state.get_memory(session_id) == []


def test_career_dna_reports_memory_fallback():
    report_id = str(uuid.uuid4())
    report = {"id": report_id, "user_id": "user-1", "summary_narrative": "great job"}
    career_dna_reports.save_report(report)

    assert career_dna_reports.get_report(report_id)["summary_narrative"] == "great job"
    mine = career_dna_reports.list_reports_for_user("user-1")
    assert any(r["id"] == report_id for r in mine)


def test_user_profile_memory_fallback_returns_none():
    # user_profile has no memory dict — it's a pure read from a table the
    # legacy flow never had a fallback for; confirms it degrades safely.
    assert user_profile.get_self_rating("user-1", "product_manager") is None
