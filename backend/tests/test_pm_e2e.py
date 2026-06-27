"""
PM Simulation End-to-End Test
Tests the full PM simulation flow with live Groq API.
Requires: uvicorn running on port 8000, GROQ_API_KEY set in .env
Run: python backend/tests/test_pm_e2e.py
"""

import requests
import json
import sys

BASE = "http://localhost:8000"

def test_pm_e2e():
    print("=" * 60)
    print("PM SIMULATION — END-TO-END TEST (live Groq)")
    print("=" * 60)

    # Test 1: Health check
    print("\n[TEST 1] Health check")
    r = requests.get(f"{BASE}/health")
    assert r.status_code == 200, f"Health check failed: {r.text}"
    health = r.json()
    print(f"  Status: {health.get('status')}")
    print(f"  Supabase: {health.get('supabase')}")
    print(f"  LLM provider: {health.get('llm_provider')}")
    print("  [PASS]")

    # Test 2: Start PM medium session
    print("\n[TEST 2] Start PM medium session")
    r = requests.post(f"{BASE}/session/start",
        json={"domain": "pm", "difficulty": "medium"})
    assert r.status_code == 200, f"Session start failed: {r.text}"
    session_data = r.json()
    session_id = session_data.get("session_id")
    assert session_id, "No session_id returned"
    assert session_data.get("opening_messages"), "No opening messages"
    assert session_data.get("voice_memo"), "No voice memo"
    print(f"  session_id: {session_id}")
    print(f"  scene: {session_data.get('current_scene_id')}")
    print(f"  opening messages: {len(session_data.get('opening_messages', []))}")
    print(f"  voice memo duration: {session_data.get('voice_memo', {}).get('duration')}")
    print(f"  hint: {session_data.get('hint')}")
    print("  [PASS]")

    # Test 3: Opening endpoint
    print("\n[TEST 3] GET /session/opening")
    r = requests.get(f"{BASE}/session/{session_id}/opening")
    assert r.status_code == 200, f"Opening failed: {r.text}"
    opening = r.json()
    assert opening.get("opening_messages"), "No opening messages from /opening"
    print(f"  opening_messages count: {len(opening.get('opening_messages', []))}")
    print(f"  voice_memo: {opening.get('voice_memo', {}).get('transcript', '')[:60]}...")
    print("  [PASS]")

    # Test 4: Clarification message → should route to npc_node only
    print("\n[TEST 4] Clarification message → npc_node route")
    r = requests.post(f"{BASE}/session/action", json={
        "session_id": session_id,
        "user_action": "Sara before I add this to the sprint, can you clarify what the success metric should be for the referral feature?"
    })
    assert r.status_code == 200, f"Action failed: {r.text}"
    action1 = r.json()
    assert action1.get("action_type") == "npc_message_clarification", \
        f"Wrong action_type: {action1.get('action_type')}"
    assert action1.get("npc_response"), "No NPC response"
    assert action1.get("score_update") is None, "Should not score NPC messages"
    print(f"  action_type: {action1.get('action_type')}")
    print(f"  Sara says: {action1.get('npc_response', '')[:100]}...")
    print(f"  trust: {action1.get('stakeholder_trust')}")
    print("  [PASS]")

    # Test 5: Branch decision → should score + NPC respond
    print("\n[TEST 5] Defer decision → score_node + npc_node route")
    r = requests.post(f"{BASE}/session/action", json={
        "session_id": session_id,
        "user_action": "I've reviewed the sprint board. We're at full capacity with 6 tickets. I'd like to push the referral feature to next sprint so we can scope it properly — I'll set up a scoping session with you for Monday."
    })
    assert r.status_code == 200, f"Action failed: {r.text}"
    action2 = r.json()
    assert action2.get("action_type") == "branch_decision_defer", \
        f"Wrong action_type: {action2.get('action_type')}"
    assert action2.get("score_update") is not None, "Missing score_update"
    assert action2.get("npc_response"), "Missing NPC response"
    score = action2.get("score_update", {})
    print(f"  action_type: {action2.get('action_type')}")
    print(f"  overall_score: {score.get('overall_score')}/100")
    print(f"  flags: {score.get('behavioural_flags')}")
    print(f"  justification: {score.get('one_line_justification')}")
    print(f"  Sara says: {action2.get('npc_response', '')[:100]}...")
    print(f"  current scores: {action2.get('current_scores')}")
    print("  [PASS]")

    # Test 6: Scene complete → transition
    print("\n[TEST 6] Scene complete → scene_transition_node")
    r = requests.post(f"{BASE}/session/action", json={
        "session_id": session_id,
        "user_action": "__scene_complete__"
    })
    assert r.status_code == 200, f"Action failed: {r.text}"
    action3 = r.json()
    assert action3.get("session_status") in \
        ["scene_complete", "simulation_complete"], \
        f"Wrong status: {action3.get('session_status')}"
    print(f"  session_status: {action3.get('session_status')}")
    print(f"  next_scene_id: {action3.get('next_scene_id')}")
    print(f"  ui_events: {[e.get('type') for e in action3.get('ui_events', [])]}")
    print("  [PASS]")

    # Test 7: State endpoint
    print("\n[TEST 7] GET /session/state")
    r = requests.get(f"{BASE}/session/{session_id}/state")
    assert r.status_code == 200, f"State failed: {r.text}"
    state = r.json()
    assert state.get("scores"), "No scores in state"
    assert state.get("decisions_log"), "No decisions in state"
    print(f"  scenes_completed: {state.get('scenes_completed')}")
    print(f"  scores: {state.get('scores')}")
    print(f"  decisions logged: {len(state.get('decisions_log', []))}")
    print("  [PASS]")

    # Test 8: Report generation
    print("\n[TEST 8] POST /report/generate")
    r = requests.post(f"{BASE}/report/generate",
        json={"session_ids": [session_id]})
    assert r.status_code == 200, f"Report failed: {r.text}"
    report_data = r.json()
    report = report_data.get("report", {})
    assert report.get("summary_narrative"), "No summary narrative"
    assert report.get("strengths"), "No strengths"
    assert report.get("growth_areas"), "No growth areas"
    assert report.get("top_recommendation"), "No top recommendation"
    assert report_data.get("fit_scores"), "No fit scores"
    assert report_data.get("ranked_domains"), "No ranked domains"
    print(f"  top_recommendation: {report.get('top_recommendation')}")
    print(f"  confidence: {report.get('confidence_level')}")
    print(f"  summary: {report.get('summary_narrative', '')[:120]}...")
    print(f"  strengths: {report.get('strengths')}")
    print(f"  growth_areas: {report.get('growth_areas')}")
    print(f"  fit_scores: {report_data.get('fit_scores')}")
    print(f"  ranked_domains: {report_data.get('ranked_domains')}")
    print("  [PASS]")

    print("\n" + "=" * 60)
    print("ALL 8 TESTS PASSED [OK]")
    print("PM simulation end-to-end verified with live Groq.")
    print("=" * 60)

if __name__ == "__main__":
    try:
        test_pm_e2e()
    except AssertionError as e:
        print(f"\n[FAIL] TEST FAILED: {e}")
        sys.exit(1)
    except requests.exceptions.ConnectionError:
        print("\n[FAIL] Cannot connect to backend.")
        print("Make sure uvicorn is running: uvicorn api:app --reload --port 8000")
        sys.exit(1)
