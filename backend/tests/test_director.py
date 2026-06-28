"""
Test Suite — Simulation Director
Tests graph structure, node routing, and state transitions
without making real LLM calls (uses mock nodes from conftest).

Run: pytest tests/test_director.py
"""

from app.agents.director import create_initial_state


def test_clarification_routes_to_npc(test_director):
    """Clarification message should route: classify → npc_node (no scoring)."""
    state = create_initial_state("test-001", "user-001")
    state["user_action"] = (
        "Hi Sara, before I add this to the sprint, "
        "can you clarify what the success metric should be?"
    )

    result = test_director.invoke(state)

    assert result["action_type"] == "npc_message_clarification"
    assert result["npc_response"] is not None
    assert result["score_update"] is None


def test_defer_routes_to_score_then_npc(test_director):
    """Defer decision should route: classify → score_node → npc_node."""
    state = create_initial_state("test-002", "user-002")
    state["user_action"] = (
        "Sara, I've looked at the sprint and we're at full capacity. "
        "I'd like to push this to next sprint so we can scope it properly."
    )

    result = test_director.invoke(state)

    assert result["action_type"] == "branch_decision_defer"
    assert result["score_update"] is not None
    assert result["npc_response"] is not None


def test_scene_complete_routes_to_transition(test_director):
    """Scene complete should route: classify → scene_transition_node."""
    state = create_initial_state("test-003", "user-003")
    state["user_action"] = "__scene_complete__"
    state["scores"] = {
        "ambiguity_tolerance": 80.0,
        "communication_clarity": 75.0,
        "stakeholder_management": 78.0,
        "analytical_reasoning": 0.0,
        "decisiveness": 0.0,
    }

    result = test_director.invoke(state)

    assert result["action_type"] == "scene_complete"
    assert result["session_status"] in ("scene_complete", "simulation_complete")


def test_blind_accept_scores_then_transitions(test_director):
    """Blind accept should score then transition directly (no NPC mid-scene)."""
    state = create_initial_state("test-004", "user-004")
    state["user_action"] = "Yes sure, let's add it, okay sounds good"

    result = test_director.invoke(state)

    assert result["action_type"] == "branch_decision_accept_blindly"
    assert result["score_update"] is not None


def test_state_structure_integrity(test_director):
    """All required state keys must be present after a scored interaction."""
    state = create_initial_state("test-005", "user-005")
    state["user_action"] = (
        "Sara, I've looked at the sprint and we're at full capacity. "
        "I'd like to push this to next sprint so we can scope it properly."
    )

    result = test_director.invoke(state)

    required_keys = [
        "session_id", "scores", "decisions_log", "stakeholder_trust",
        "npc_states", "current_scene_id", "session_status",
    ]
    for key in required_keys:
        assert key in result, f"Missing key: {key}"

    assert len(result["decisions_log"]) > 0
