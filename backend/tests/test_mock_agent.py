import pytest
"""
Test Suite — app.services.mock_agent
Deterministic mock scene/evaluation/fit-report/MCQ generation, validated
against the contract models in agent_contracts.py. No DB, no LLM calls.

Run: pytest tests/test_mock_agent.py
"""
from app.schemas.agent_contracts import (
    EvaluationContext,
    EvaluationResult,
    FitReportContext,
    FitReportResult,
    HistoryEntry,
    MCQGenerationContext,
    MCQGenerationResult,
    SceneContent,
    SceneGenerationContext,
    ScoredEvaluation,
    SessionEvaluationSummary,
    SubmittedResponse,
    UserProfileSnippet,
)
from app.services import mock_agent


def _scene_ctx(scene_number=1, history=None):
    return SceneGenerationContext(
        simulation_session_id="sess-1",
        user_id="user-1",
        domain="product_manager",
        difficulty="medium",
        scene_number=scene_number,
        user_profile_snippet=UserProfileSnippet(self_rating=4, core_interests=["ux"]),
        history=history or [],
    )


def _eval_ctx(scene, raw_text="a thoughtful response"):
    return EvaluationContext(
        simulation_session_id="sess-1",
        user_id="user-1",
        domain="product_manager",
        difficulty="medium",
        scene_number=scene.scene_number,
        scene_content=scene,
        user_response=SubmittedResponse(raw_text=raw_text),
    )


@pytest.mark.anyio
async def test_generate_scene_returns_valid_scene_content():
    scene = await mock_agent.generate_scene(_scene_ctx(scene_number=1))

    assert isinstance(scene, SceneContent)
    assert scene.scene_number == 1
    assert scene.domain == "product_manager"
    assert scene.difficulty == "medium"
    assert scene.is_final_scene is False


@pytest.mark.anyio
async def test_generate_scene_marks_final_at_total_scenes():
    scene = await mock_agent.generate_scene(_scene_ctx(scene_number=mock_agent.MOCK_TOTAL_SCENES))
    assert scene.is_final_scene is True

    scene_before = await mock_agent.generate_scene(_scene_ctx(scene_number=mock_agent.MOCK_TOTAL_SCENES - 1))
    assert scene_before.is_final_scene is False


@pytest.mark.anyio
async def test_evaluate_response_returns_valid_evaluation_result():
    scene = await mock_agent.generate_scene(_scene_ctx(scene_number=1))
    result = await mock_agent.evaluate_response(_eval_ctx(scene))

    assert isinstance(result, EvaluationResult)
    assert 0 <= result.overall_score <= 100
    assert set(result.dimension_scores.keys()) == {
        "analytical_reasoning", "ambiguity_tolerance", "communication_clarity",
        "attention_to_detail", "decisiveness",
    }
    assert len(result.npc_state_updates) == 1


@pytest.mark.anyio
async def test_evaluate_response_score_deterministic_on_input_length():
    scene = await mock_agent.generate_scene(_scene_ctx(scene_number=1))
    result_a = await mock_agent.evaluate_response(_eval_ctx(scene, raw_text="short"))
    result_b = await mock_agent.evaluate_response(_eval_ctx(scene, raw_text="short"))
    result_c = await mock_agent.evaluate_response(_eval_ctx(scene, raw_text="a much longer response text"))

    assert result_a.overall_score == result_b.overall_score
    assert result_c.overall_score >= result_a.overall_score


@pytest.mark.anyio
async def test_evaluate_response_handles_empty_response_text():
    scene = await mock_agent.generate_scene(_scene_ctx(scene_number=1))
    result = await mock_agent.evaluate_response(_eval_ctx(scene, raw_text=""))
    assert 0 <= result.overall_score <= 100


@pytest.mark.anyio
async def test_generate_fit_report_returns_valid_result():
    scene = await mock_agent.generate_scene(_scene_ctx(scene_number=1))
    evaluation = await mock_agent.evaluate_response(_eval_ctx(scene, raw_text="a solid response here"))

    ctx = FitReportContext(
        user_id="user-1",
        sessions=[
            SessionEvaluationSummary(
                simulation_session_id="sess-1",
                domain="product_manager",
                difficulty="medium",
                evaluations=[
                    ScoredEvaluation(scene_evaluation_id="eval-1", scene_number=1, result=evaluation)
                ],
            )
        ],
    )
    result = await mock_agent.generate_fit_report(ctx)

    assert isinstance(result, FitReportResult)
    assert result.top_recommendation in result.ranked_domains
    assert len(result.ranked_domains) == 5
    assert result.confidence_level in ("high", "moderate", "directional")
    # evidence citations must point at the real scene_evaluation_id supplied
    cited_ids = {cid for ids in result.evidence_citations.values() for cid in ids}
    assert cited_ids <= {"eval-1"}


@pytest.mark.anyio
async def test_generate_fit_report_handles_no_evaluations():
    ctx = FitReportContext(user_id="user-1", sessions=[])
    result = await mock_agent.generate_fit_report(ctx)

    assert isinstance(result, FitReportResult)
    assert result.dimension_scores == {}
    assert result.confidence_level == "directional"


@pytest.mark.anyio
async def test_generate_mcqs_returns_five_questions():
    ctx = MCQGenerationContext(
        user_id="user-1",
        chosen_field="sqa_engineer",
        self_assessment=[],
    )
    result = await mock_agent.generate_mcqs(ctx)

    assert isinstance(result, MCQGenerationResult)
    assert len(result.questions) == 5
    for q in result.questions:
        assert len(q.options) == 4
        assert 0 <= q.correct_option_index < 4


@pytest.mark.anyio
async def test_history_entry_round_trips_through_scene_and_evaluation():
    scene = await mock_agent.generate_scene(_scene_ctx(scene_number=1))
    evaluation = await mock_agent.evaluate_response(_eval_ctx(scene))
    entry = HistoryEntry(scene=scene, evaluation=evaluation)

    assert entry.scene.scene_number == 1
    assert entry.evaluation.overall_score == evaluation.overall_score
