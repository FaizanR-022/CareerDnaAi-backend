"""
Compatibility shim for app.agents.director.

The old director.py was removed in the LangGraph migration (commit 272b040).
This module re-exports create_initial_state for backward compatibility with
existing tests while the test suite is migrated to the new graph architecture.
"""
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def create_initial_state(
    session_id: str,
    user_id: str,
    domain: str = "product_manager",
    difficulty: str = "medium",
) -> dict:
    """
    Compatibility shim — creates a minimal SimulationState dict for tests.
    The real production entry points are run_scenario_step() and
    run_evaluation_step() in app.agents.graph.
    """
    return {
        "session_id": session_id,
        "simulation_session_id": session_id,
        "user_id": user_id,
        "domain": domain,
        "difficulty": difficulty,
        "active_domain": domain,
        "current_scene_id": "scene_1",
        "scene_number": 1,
        "scenes_completed": [],
        "session_status": "active",
        "sprint_progress": 0,
        "time_remaining": None,
        "stakeholder_trust": {
            "sara_khan": 50,
            "mr_jawaid": 50,
            "zara_malik": 50,
        },
        "scores": {
            "analytical_reasoning": 0.0,
            "ambiguity_tolerance": 0.0,
            "communication_clarity": 0.0,
            "attention_to_detail": 0.0,
            "decisiveness": 0.0,
        },
        "decisions_log": [],
        "npc_states": {
            "sara_khan": {
                "last_interaction_summary": "No prior interaction.",
                "relationship_score": 50,
                "current_sentiment": "neutral",
                "key_events_memory": [],
            },
        },
        "user_action": "",
        "action_type": "",
        "npc_response": None,
        "score_update": None,
        "next_scene_id": None,
        "ui_events": [],
        "user_profile": {"user_id": user_id},
        # New LangGraph state fields
        "current_scene": None,
        "current_evaluation": None,
        "latest_score": 0.0,
        "should_loop_back": False,
        "lowered_difficulty": None,
        "fit_scores": None,
        "career_fit_matrix": None,
        "report": None,
        "is_final_scene": False,
        "loop_count": 0,
        "history": [],
        "student_response": "",
    }
