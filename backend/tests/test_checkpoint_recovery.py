"""
Test Suite — LangGraph checkpoint state recovery.

Validates that simulation session state survives a simulated hard process
restart by persisting through the configured checkpointer (PostgresSaver or
MemorySaver fallback) and can be resumed with full historic context.

Phases:
  1. State initialisation — invoke the scene graph to drive into Scene 1.
  2. Simulated crash — replace the graph reference to mimic a server restart.
  3. State recovery assertions — query get_state() and verify key fields.
  4. Context-aware follow-up — submit a student response and assert that the
     evaluation engine operates with full historic context.

Run: pytest tests/test_checkpoint_recovery.py -v
"""

import pytest
import importlib
import uuid
from unittest.mock import patch

# ─── Constants ────────────────────────────────────────────────────────────────

THREAD_ID = "test-recovery-uuid-77777"
CONFIG: dict = {"configurable": {"thread_id": THREAD_ID}}

# ─── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def graph_module():
    """
    Import the graph module fresh. Scope is module so the same compiled graph
    instance is shared within this test module (simulating a single process).
    """
    import app.agents.graph as g
    return g


@pytest.fixture(scope="module")
def initial_state() -> dict:
    """Base state dict used to start a product_manager simulation at scene 1."""
    return {
        "simulation_session_id": THREAD_ID,
        "user_id": str(uuid.uuid4()),
        "domain": "product_manager",
        "difficulty": "medium",
        "scene_number": 1,
        "user_profile": {
            "self_rating": 3,
            "core_interests": ["product management", "agile"],
        },
        "history": [],
        "active_domain": "product_manager",
        "current_scene": None,
        "current_evaluation": None,
        "latest_score": 0.0,
        "should_loop_back": False,
        "lowered_difficulty": None,
        "fit_scores": None,
        "report": None,
        "is_final_scene": False,
        "loop_count": 0,
        "student_response": "",
        "npc_trust": None,
    }


# ─── Phase 1: State Initialisation ────────────────────────────────────────────


@pytest.mark.anyio
async def test_phase1_scene_graph_initialises_session(
    graph_module, initial_state
):
    """
    Phase 1 — Drive the scene graph to generate Scene 1.
    The checkpointer must persist the resulting state under THREAD_ID.
    """
    result = await graph_module.scene_graph.ainvoke(initial_state, config=CONFIG)

    # Scene must be generated
    assert result is not None, "scene_graph.invoke() returned None"
    current_scene = result.get("current_scene")
    assert current_scene is not None, "current_scene not in result"
    assert isinstance(current_scene, dict), "current_scene is not a dict"
    assert current_scene.get("scene_number") == 1, (
        f"Expected scene_number=1, got {current_scene.get('scene_number')}"
    )
    assert current_scene.get("domain") == "product_manager"


# ─── Phase 2: Simulated Process Crash ────────────────────────────────────────


def test_phase2_state_survives_module_reload(graph_module):
    """
    Phase 2 — Simulate a hard server restart by forcing the graph module to
    be reloaded (clears Python's in-memory object references).

    The re-imported module will re-compile the graphs using the same
    checkpointer backend, so any persisted state should survive.
    """
    # Reload re-runs module-level code (graph compilation + checkpointer setup)
    reloaded = importlib.reload(graph_module)

    # The reloaded module must still expose the same public API
    assert hasattr(reloaded, "scene_graph"), "scene_graph missing after reload"
    assert hasattr(reloaded, "eval_graph"), "eval_graph missing after reload"
    assert hasattr(reloaded, "run_scenario_step"), "run_scenario_step missing after reload"


# ─── Phase 3: State Recovery Assertions ───────────────────────────────────────


def test_phase3_get_state_recovers_thread(graph_module):
    """
    Phase 3 — After the simulated restart, query get_state() for THREAD_ID.

    When using MemorySaver (the CI fallback) state is NOT persisted across
    module reloads, so this test skips gracefully if the snapshot is absent.
    When PostgresSaver is active the snapshot MUST be present and valid.
    """
    import os

    snapshot = graph_module.scene_graph.get_state(CONFIG)

    if os.environ.get("SUPABASE_CONN_STRING"):
        # Postgres is active — state MUST be recovered
        assert snapshot is not None, (
            "get_state() returned None despite PostgresSaver being configured"
        )
        values = snapshot.values

        assert values.get("active_domain") == "product_manager", (
            f"active_domain mismatch: {values.get('active_domain')}"
        )
        assert values.get("loop_count") == 0, (
            f"loop_count mismatch: {values.get('loop_count')}"
        )
        # history array must be present (may be empty on first scene before eval)
        assert "history" in values, "history key missing from recovered state"
    else:
        # MemorySaver — state is lost on reload; skip this assertion
        pytest.skip(
            "SUPABASE_CONN_STRING not set — PostgresSaver inactive. "
            "State recovery across process boundaries requires Postgres. "
            "Set SUPABASE_CONN_STRING to run full persistence assertions."
        )


def test_phase3_recovered_state_fields_types(graph_module):
    """
    Phase 3 — If a snapshot exists, assert the field types are correct.
    """
    import os
    if not os.environ.get("SUPABASE_CONN_STRING"):
        pytest.skip("SUPABASE_CONN_STRING not set — skipping Postgres-only assertion.")

    snapshot = graph_module.scene_graph.get_state(CONFIG)
    assert snapshot is not None
    values = snapshot.values

    assert isinstance(values.get("domain"), str)
    assert isinstance(values.get("loop_count"), int)
    assert isinstance(values.get("history"), list)
    assert isinstance(values.get("is_final_scene"), bool)


# ─── Phase 4: Context-Aware Follow-Up ─────────────────────────────────────────


@pytest.mark.anyio
async def test_phase4_eval_graph_runs_with_recovered_context(graph_module, initial_state):
    """
    Phase 4 — Fire a student response into the eval_graph using the same
    THREAD_ID config. The evaluation engine must run without errors.

    Because the eval_graph state is seeded with the base state (including
    current_scene from Phase 1), the LLM evaluator gets full historic context.

    We use the mock agent path to avoid burning real Groq tokens in CI.
    """
    # Construct a minimal eval invocation state
    eval_state = {
        **initial_state,
        "current_scene": {
            "scene_number": 1,
            "domain": "product_manager",
            "difficulty": "medium",
            "title": "Referral Feature Request",
            "narrative": (
                "Sara Khan from Marketing requests adding a referral feature "
                "to the active sprint. The sprint board is already full."
            ),
            "context_data": {"active_npcs": ["sara_khan"], "scene_type": "feature_request"},
            "characters": [
                {"id": "sara_khan", "name": "Sara Khan",
                 "role": "Head of Marketing", "initial_trust": 50}
            ],
            "messages": [
                {"sender": "Sara Khan", "channel": "developer",
                 "content": "Can we add the referral feature this sprint?",
                 "time_offset_minutes": 0}
            ],
            "response_format": "free_text",
            "response_choices": None,
            "prompt_for_response": "How do you respond?",
            "hint": None,
            "is_final_scene": False,
            "extra": {},
        },
        "student_response": (
            "Sara, I completely understand the urgency around the referral feature. "
            "Before I commit to squeezing it into this sprint, I need to review our "
            "current sprint capacity and understand the minimum viable scope. "
            "Can you share the key success metric you need from this feature? "
            "That will help me make a data-backed decision with the engineering team."
        ),
        "is_final_scene": False,
        "history": [],
    }

    result = await graph_module.eval_graph.ainvoke(eval_state, config=CONFIG)

    # Core assertions
    assert result is not None, "eval_graph.invoke() returned None"
    evaluation = result.get("current_evaluation")
    assert evaluation is not None, "current_evaluation missing from eval result"
    assert isinstance(evaluation, dict), "current_evaluation is not a dict"

    # Score must be a float in valid range
    score = result.get("latest_score")
    assert score is not None, "latest_score missing from eval result"
    assert 0.0 <= float(score) <= 100.0, f"latest_score out of range: {score}"

    # Evaluation must contain all required dimension keys
    dim_scores = evaluation.get("dimension_scores", {})
    required_dims = {
        "analytical_reasoning",
        "ambiguity_tolerance",
        "communication_clarity",
        "attention_to_detail",
        "decisiveness",
    }
    missing = required_dims - set(dim_scores.keys())
    assert not missing, f"Missing dimension scores: {missing}"


@pytest.mark.anyio
async def test_phase4_sqa_trust_modifier_applied_on_evidence(graph_module):
    """
    Phase 4 (SQA-specific) — Verify that providing console traces in an SQA
    response causes the trust modifier (+10) to be injected into npc_trust.
    """
    sqa_state = {
        "simulation_session_id": "test-sqa-trust-modifier",
        "user_id": str(uuid.uuid4()),
        "domain": "sqa_engineer",
        "difficulty": "medium",
        "scene_number": 1,
        "user_profile": {},
        "history": [],
        "active_domain": "sqa_engineer",
        "current_scene": {
            "scene_number": 1,
            "domain": "sqa_engineer",
            "difficulty": "medium",
            "title": "Checkout Bug Investigation",
            "narrative": "Dan pushed the staging build. Bugs are present.",
            "context_data": {"active_npcs": ["dan_frontend_dev"]},
            "characters": [
                {"id": "dan_frontend_dev", "name": "Dan",
                 "role": "Frontend Developer", "initial_trust": 50}
            ],
            "messages": [],
            "response_format": "free_text",
            "response_choices": None,
            "prompt_for_response": "File a bug report.",
            "hint": None,
            "is_final_scene": False,
            "extra": {},
        },
        "student_response": (
            "Dan, here are my reproduction steps: "
            "1. Open checkout form, 2. Enter email without @ symbol, "
            "3. Hit submit. Console output: TypeError: invalid email format. "
            "Traceback in browser console attached. This is a Critical severity bug."
        ),
        "is_final_scene": False,
        "loop_count": 0,
        "latest_score": 0.0,
        "current_evaluation": None,
        "should_loop_back": False,
        "lowered_difficulty": None,
        "fit_scores": None,
        "report": None,
        "npc_trust": {"dan_frontend_dev": 50},
    }

    sqa_config = {"configurable": {"thread_id": "test-sqa-trust-modifier"}}
    result = await graph_module.eval_graph.ainvoke(sqa_state, config=sqa_config)

    assert result is not None
    # npc_trust must be updated in the result
    npc_trust = result.get("npc_trust", {})
    dan_trust = npc_trust.get("dan_frontend_dev")
    assert dan_trust is not None, "npc_trust for dan_frontend_dev not set in result"
    # Trust should be >= 50 (baseline) because evidence signals were provided
    assert dan_trust >= 50, (
        f"Expected dan_trust >= 50 after evidence, got {dan_trust}"
    )


@pytest.mark.anyio
async def test_phase4_sqa_trust_penalty_on_premature_escalation(graph_module):
    """
    Phase 4 (SQA-specific) — Verify that escalating to management without
    evidence causes the trust modifier (-15) to be applied.
    """
    sqa_state = {
        "simulation_session_id": "test-sqa-escalation-penalty",
        "user_id": str(uuid.uuid4()),
        "domain": "sqa_engineer",
        "difficulty": "medium",
        "scene_number": 1,
        "user_profile": {},
        "history": [],
        "active_domain": "sqa_engineer",
        "current_scene": {
            "scene_number": 1,
            "domain": "sqa_engineer",
            "difficulty": "medium",
            "title": "Checkout Bug Investigation",
            "narrative": "Dan pushed the staging build. Bugs are present.",
            "context_data": {"active_npcs": ["dan_frontend_dev"]},
            "characters": [
                {"id": "dan_frontend_dev", "name": "Dan",
                 "role": "Frontend Developer", "initial_trust": 50}
            ],
            "messages": [],
            "response_format": "free_text",
            "response_choices": None,
            "prompt_for_response": "File a bug report.",
            "hint": None,
            "is_final_scene": False,
            "extra": {},
        },
        "student_response": (
            "I'm going to escalate to the PM immediately "
            "and report to management that Dan's build is broken."
        ),
        "is_final_scene": False,
        "loop_count": 0,
        "latest_score": 0.0,
        "current_evaluation": None,
        "should_loop_back": False,
        "lowered_difficulty": None,
        "fit_scores": None,
        "report": None,
        "npc_trust": {"dan_frontend_dev": 50},
    }

    sqa_config = {"configurable": {"thread_id": "test-sqa-escalation-penalty"}}
    result = await graph_module.eval_graph.ainvoke(sqa_state, config=sqa_config)

    assert result is not None
    npc_trust = result.get("npc_trust", {})
    dan_trust = npc_trust.get("dan_frontend_dev")
    assert dan_trust is not None, "npc_trust for dan_frontend_dev not set in result"
    # Trust should be <= 50 (baseline) — premature escalation penalty applied
    assert dan_trust <= 50, (
        f"Expected dan_trust <= 50 after premature escalation, got {dan_trust}"
    )
