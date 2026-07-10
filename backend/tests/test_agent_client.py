"""
Test Suite — app.services.agent_client
The mock/real dispatch shim. No DB, no LLM calls.

Run: pytest tests/test_agent_client.py
"""
import pytest

from app.core.config import get_settings
from app.schemas.agent_contracts import (
    EvaluationContext,
    FitReportContext,
    MCQGenerationContext,
    SceneGenerationContext,
    SubmittedResponse,
    UserProfileSnippet,
)
from app.services import agent_client, mock_agent


@pytest.fixture(autouse=True)
def reset_impl():
    yield
    get_settings.cache_clear()


def _scene_ctx():
    return SceneGenerationContext(
        simulation_session_id="s1", user_id="u1", domain="product_manager",
        difficulty="medium", scene_number=1,
        user_profile_snippet=UserProfileSnippet(),
    )


def test_generate_scene_dispatches_to_mock_by_default():
    scene = agent_client.generate_scene(_scene_ctx())
    assert scene.scene_number == 1


def test_evaluate_response_dispatches_to_mock_by_default():
    scene = mock_agent.generate_scene(_scene_ctx())
    ctx = EvaluationContext(
        simulation_session_id="s1", user_id="u1", domain="product_manager",
        difficulty="medium", scene_number=1, scene_content=scene,
        user_response=SubmittedResponse(raw_text="hello"),
    )
    result = agent_client.evaluate_response(ctx)
    assert 0 <= result.overall_score <= 100


def test_generate_fit_report_dispatches_to_mock_by_default():
    ctx = FitReportContext(user_id="u1", sessions=[])
    result = agent_client.generate_fit_report(ctx)
    assert result.confidence_level == "directional"


def test_generate_mcqs_dispatches_to_mock_by_default():
    ctx = MCQGenerationContext(user_id="u1", chosen_field="data_analyst", self_assessment=[])
    result = agent_client.generate_mcqs(ctx)
    assert len(result.questions) == 5


def test_generate_scene_raises_when_real_not_wired(monkeypatch):
    monkeypatch.setenv("AGENT_LAYER_IMPL", "real")
    get_settings.cache_clear()

    with pytest.raises(NotImplementedError):
        agent_client.generate_scene(_scene_ctx())


def test_evaluate_response_raises_when_real_not_wired(monkeypatch):
    monkeypatch.setenv("AGENT_LAYER_IMPL", "real")
    get_settings.cache_clear()

    scene = mock_agent.generate_scene(_scene_ctx())
    ctx = EvaluationContext(
        simulation_session_id="s1", user_id="u1", domain="product_manager",
        difficulty="medium", scene_number=1, scene_content=scene,
        user_response=SubmittedResponse(raw_text="hello"),
    )
    with pytest.raises(NotImplementedError):
        agent_client.evaluate_response(ctx)


def test_generate_fit_report_raises_when_real_not_wired(monkeypatch):
    monkeypatch.setenv("AGENT_LAYER_IMPL", "real")
    get_settings.cache_clear()

    with pytest.raises(NotImplementedError):
        agent_client.generate_fit_report(FitReportContext(user_id="u1", sessions=[]))


def test_generate_mcqs_raises_when_real_not_wired(monkeypatch):
    monkeypatch.setenv("AGENT_LAYER_IMPL", "real")
    get_settings.cache_clear()

    ctx = MCQGenerationContext(user_id="u1", chosen_field="data_analyst", self_assessment=[])
    with pytest.raises(NotImplementedError):
        agent_client.generate_mcqs(ctx)
