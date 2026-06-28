"""
PM Simulation End-to-End Test
Tests the full PM simulation flow with live Groq API.
Requires: uvicorn running on port 8000, GROQ_API_KEY set in .env

Run: pytest tests/test_pm_e2e.py
Skip condition: server not reachable on localhost:8000
"""

import pytest
import requests

BASE = "http://localhost:8000"


def _server_available() -> bool:
    try:
        requests.get(f"{BASE}/health", timeout=2)
        return True
    except requests.exceptions.ConnectionError:
        return False


pytestmark = pytest.mark.skipif(
    not _server_available(),
    reason="Backend server not running on localhost:8000",
)


@pytest.fixture(scope="module")
def session_id():
    r = requests.post(f"{BASE}/session/start", json={"domain": "pm", "difficulty": "medium"})
    assert r.status_code == 200, f"Session start failed: {r.text}"
    return r.json()["session_id"]


def test_health():
    r = requests.get(f"{BASE}/health")
    assert r.status_code == 200
    health = r.json()
    assert health.get("status") == "ok"


def test_start_pm_medium_session():
    r = requests.post(f"{BASE}/session/start", json={"domain": "pm", "difficulty": "medium"})
    assert r.status_code == 200, f"Session start failed: {r.text}"
    data = r.json()
    assert data.get("session_id")
    assert data.get("opening_messages")
    assert data.get("voice_memo")


def test_opening_endpoint(session_id):
    r = requests.get(f"{BASE}/session/{session_id}/opening")
    assert r.status_code == 200, f"Opening failed: {r.text}"
    opening = r.json()
    assert opening.get("opening_messages")


def test_clarification_routes_to_npc(session_id):
    r = requests.post(f"{BASE}/session/action", json={
        "session_id": session_id,
        "user_action": (
            "Sara before I add this to the sprint, can you clarify "
            "what the success metric should be for the referral feature?"
        ),
    })
    assert r.status_code == 200, f"Action failed: {r.text}"
    data = r.json()
    assert data.get("action_type") == "npc_message_clarification"
    assert data.get("npc_response")
    assert data.get("score_update") is None


def test_defer_scores_and_npc_responds(session_id):
    r = requests.post(f"{BASE}/session/action", json={
        "session_id": session_id,
        "user_action": (
            "I've reviewed the sprint board. We're at full capacity with 6 tickets. "
            "I'd like to push the referral feature to next sprint so we can scope it "
            "properly — I'll set up a scoping session with you for Monday."
        ),
    })
    assert r.status_code == 200, f"Action failed: {r.text}"
    data = r.json()
    assert data.get("action_type") == "branch_decision_defer"
    assert data.get("score_update") is not None
    assert data.get("npc_response")


def test_scene_complete_transitions(session_id):
    r = requests.post(f"{BASE}/session/action", json={
        "session_id": session_id,
        "user_action": "__scene_complete__",
    })
    assert r.status_code == 200, f"Action failed: {r.text}"
    data = r.json()
    assert data.get("session_status") in ("scene_complete", "simulation_complete")


def test_state_endpoint(session_id):
    r = requests.get(f"{BASE}/session/{session_id}/state")
    assert r.status_code == 200, f"State failed: {r.text}"
    state = r.json()
    assert state.get("scores")
    assert state.get("decisions_log")


def test_report_generation(session_id):
    r = requests.post(f"{BASE}/report/generate", json={"session_ids": [session_id]})
    assert r.status_code == 200, f"Report failed: {r.text}"
    data = r.json()
    report = data.get("report", {})
    assert report.get("summary_narrative")
    assert report.get("strengths")
    assert report.get("growth_areas")
    assert report.get("top_recommendation")
    assert data.get("fit_scores")
    assert data.get("ranked_domains")
