import sys
from pathlib import Path

# Make `app` importable when running pytest from the backend/ directory
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from langgraph.graph import END, StateGraph

from app.agents.director import (
    SimulationState,
    classify_node,
    create_initial_state,
    route_after_classify,
    route_after_score,
    scene_transition_node,
)


# ─── MOCK NODES ──────────────────────────────────────────────────────────────

def mock_score_node(state: SimulationState) -> dict:
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
    updated_scores = {
        "ambiguity_tolerance": 80.0,
        "communication_clarity": 75.0,
        "stakeholder_management": 78.0,
        "analytical_reasoning": 0.0,
        "decisiveness": 0.0,
    }
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
    dialogue = (
        "Oh great question! The main goal is to make it easy for users to invite friends "
        "via a link. I'm flexible on the exact design — what do you think is feasible?"
    )
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


# ─── FIXTURES ────────────────────────────────────────────────────────────────

@pytest.fixture
def test_director():
    """Director graph with mock LLM nodes — no Groq API key required."""
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


@pytest.fixture
def initial_state():
    """Fresh simulation state for the pm domain."""
    return create_initial_state("test-session", "test-user")
