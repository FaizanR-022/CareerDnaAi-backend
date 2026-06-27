"""
NOTE: THIS IS JUST A BASIC PROTOTYPE THAT JUST DEMONSTRATES ORCHESTRATION
BOGGEST ISSUE: DIRECTOR+NPC AND NOT DIRECTOR+6 AGENTS

Test Script — Simulation Director
Tests graph structure, node routing, and state transitions
WITHOUT making real LLM calls (uses mock LLM responses).
Run: python test_director.py
"""

import json
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from langgraph.graph import StateGraph, END
from agents.director import (
    SimulationState,
    classify_node,
    scene_transition_node,
    route_after_classify,
    route_after_score,
    route_after_npc,
    build_director,
    create_initial_state,
    PM_SCENARIO,
)

# ─── MOCK NODES (replace LLM nodes for testing) ───────────────────────────────

def mock_score_node(state: SimulationState) -> dict:
    """Returns a fake score without calling Groq."""
    print(f"  [MOCK score_node] scoring: '{state['user_action'][:60]}'")
    score_data = {
        "overall_score": 78,
        "dimension_scores": {
            "ambiguity_tolerance": 80,
            "communication_clarity": 75,
            "stakeholder_management": 78,
        },
        "behavioural_flags": ["clarification_sought"],
        "one_line_justification": "Student asked for clarification before committing.",
    }
    updated_scores = {"ambiguity_tolerance": 80.0, "communication_clarity": 75.0,
                      "stakeholder_management": 78.0, "analytical_reasoning": 0.0, "decisiveness": 0.0}
    updated_log = list(state["decisions_log"]) + [{
        "scene_id": state["current_scene_id"],
        "action": state["user_action"],
        "score": 78,
        "flags": ["clarification_sought"],
    }]
    return {
        "scores": updated_scores,
        "decisions_log": updated_log,
        "score_update": score_data,
        "ui_events": state["ui_events"] + [{"type": "score_update", "data": score_data}],
    }


def mock_npc_node(state: SimulationState) -> dict:
    """Returns a fake NPC response without calling Groq."""
    print(f"  [MOCK npc_node] Sara responds to: '{state['user_action'][:60]}'")
    dialogue = "Oh great question! The main goal is to make it easy for users to invite friends via a link. I'm flexible on the exact design — what do you think is feasible?"
    updated_trust = dict(state["stakeholder_trust"])
    updated_trust["sara_khan"] = min(100, updated_trust.get("sara_khan", 50) + 5)
    return {
        "npc_response": dialogue,
        "npc_states": state["npc_states"],
        "stakeholder_trust": updated_trust,
        "ui_events": state["ui_events"] + [
            {"type": "npc_message", "npc_id": "sara_khan", "dialogue": dialogue},
            {"type": "trust_update", "npc_id": "sara_khan", "value": updated_trust["sara_khan"]},
        ],
    }


def build_test_director():
    """Builds director graph with mock LLM nodes for testing."""
    graph = StateGraph(SimulationState)
    graph.add_node("classify_node", classify_node)
    graph.add_node("score_node", mock_score_node)
    graph.add_node("npc_node", mock_npc_node)
    graph.add_node("scene_transition_node", scene_transition_node)
    graph.set_entry_point("classify_node")
    graph.add_conditional_edges("classify_node", route_after_classify, {
        "score_node": "score_node",
        "npc_node": "npc_node",
        "scene_transition_node": "scene_transition_node",
    })
    graph.add_conditional_edges("score_node", route_after_score, {
        "npc_node": "npc_node",
        "scene_transition_node": "scene_transition_node",
    })
    graph.add_edge("npc_node", END)
    graph.add_edge("scene_transition_node", END)
    return graph.compile()


# ─── TEST CASES ───────────────────────────────────────────────────────────────

def run_tests():
    print("=" * 60)
    print("SIMULATION DIRECTOR — TEST SUITE")
    print("=" * 60)

    director = build_test_director()

    # ── Test 1: Clarification message → NPC response ──────────────────────────
    print("\n[TEST 1] Clarification message should route: classify → npc_node")
    state = create_initial_state("test-001", "user-001")
    state["user_action"] = "Hi Sara, before I add this to the sprint, can you clarify what the success metric should be?"

    result = director.invoke(state)

    assert result["action_type"] == "npc_message_clarification", f"Expected npc_message_clarification, got {result['action_type']}"
    assert result["npc_response"] is not None, "NPC response should not be None"
    assert result["score_update"] is None, "No score update for pure NPC messages"
    print(f"  ✓ action_type: {result['action_type']}")
    print(f"  ✓ Sara responds: '{result['npc_response'][:80]}...'")
    print(f"  ✓ trust updated: {result['stakeholder_trust']}")

    # ── Test 2: Branch decision → score + NPC ─────────────────────────────────
    print("\n[TEST 2] Defer decision should route: classify → score_node → npc_node")
    state2 = create_initial_state("test-002", "user-002")
    state2["user_action"] = "Sara, I've looked at the sprint and we're at full capacity. I'd like to push this to next sprint so we can scope it properly."

    result2 = director.invoke(state2)

    assert result2["action_type"] == "branch_decision_defer", f"Expected branch_decision_defer, got {result2['action_type']}"
    assert result2["score_update"] is not None, "Score update should exist for decisions"
    assert result2["npc_response"] is not None, "NPC should respond after decision"
    print(f"  ✓ action_type: {result2['action_type']}")
    print(f"  ✓ score: {result2['score_update']['overall_score']}/100")
    print(f"  ✓ flags: {result2['score_update']['behavioural_flags']}")
    print(f"  ✓ Sara responds: '{result2['npc_response'][:80]}...'")

    # ── Test 3: Scene complete → transition ────────────────────────────────────
    print("\n[TEST 3] Scene complete should route: classify → scene_transition_node")
    state3 = create_initial_state("test-003", "user-003")
    state3["user_action"] = "__scene_complete__"
    state3["scores"] = {"ambiguity_tolerance": 80.0, "communication_clarity": 75.0,
                        "stakeholder_management": 78.0, "analytical_reasoning": 0.0, "decisiveness": 0.0}

    result3 = director.invoke(state3)

    assert result3["action_type"] == "scene_complete", f"Expected scene_complete, got {result3['action_type']}"
    assert result3["session_status"] in ("scene_complete", "simulation_complete")
    print(f"  ✓ action_type: {result3['action_type']}")
    print(f"  ✓ session_status: {result3['session_status']}")
    print(f"  ✓ ui_events: {[e['type'] for e in result3['ui_events']]}")

    # ── Test 4: Blind accept → score → scene transition ────────────────────────
    print("\n[TEST 4] Blind accept should score then transition (no NPC mid-scene)")
    state4 = create_initial_state("test-004", "user-004")
    state4["user_action"] = "Yes sure, let's add it, okay sounds good"

    result4 = director.invoke(state4)

    assert result4["action_type"] == "branch_decision_accept_blindly"
    assert result4["score_update"] is not None, "Blind accept should still be scored"
    print(f"  ✓ action_type: {result4['action_type']}")
    print(f"  ✓ score: {result4['score_update']['overall_score']}/100")
    print(f"  ✓ session_status: {result4['session_status']}")

    # ── Test 5: State inspection ───────────────────────────────────────────────
    print("\n[TEST 5] State structure integrity check")
    final_state = result2  # use the scored state from test 2
    required_keys = ["session_id", "scores", "decisions_log", "stakeholder_trust",
                     "npc_states", "current_scene_id", "session_status"]
    for key in required_keys:
        assert key in final_state, f"Missing key: {key}"
    print(f"  ✓ All required state keys present: {required_keys}")
    print(f"  ✓ decisions_log has {len(final_state['decisions_log'])} entries")
    print(f"  ✓ scores: {final_state['scores']}")

    print("\n" + "=" * 60)
    print("ALL 5 TESTS PASSED ✓")
    print("Graph structure, routing, and state transitions verified.")
    print("LLM calls tested with mocks — no Groq API key required for tests.")
    print("=" * 60)


if __name__ == "__main__":
    run_tests()
