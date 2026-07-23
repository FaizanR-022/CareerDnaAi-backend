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


import uuid

def _scene_ctx():
    return SceneGenerationContext(
        simulation_session_id=str(uuid.uuid4()), user_id="u1", domain="product_manager",
        difficulty="medium", scene_number=1,
        user_profile_snippet=UserProfileSnippet(),
    )


@pytest.mark.anyio
async def test_generate_scene_dispatches_to_mock_by_default():
    scene = await agent_client.generate_scene(_scene_ctx())
    assert scene.scene_number == 1


@pytest.mark.anyio
async def test_evaluate_response_dispatches_to_mock_by_default():
    scene_ctx = _scene_ctx()
    scene = await agent_client.generate_scene(scene_ctx)
    ctx = EvaluationContext(
        simulation_session_id=scene_ctx.simulation_session_id, user_id="u1", domain="product_manager",
        difficulty="medium", scene_number=1, scene_content=scene,
        user_response=SubmittedResponse(raw_text="hello"),
    )
    result = await agent_client.evaluate_response(ctx)
    assert 0 <= result.overall_score <= 100


@pytest.mark.anyio
async def test_generate_fit_report_dispatches_to_mock_by_default():
    ctx = FitReportContext(user_id="u1", sessions=[])
    result = await agent_client.generate_fit_report(ctx)
    assert result.confidence_level == "directional"


@pytest.mark.anyio
async def test_generate_mcqs_dispatches_to_mock_by_default():
    ctx = MCQGenerationContext(user_id="u1", chosen_field="data_analyst", self_assessment=[])
    result = await agent_client.generate_mcqs(ctx)
    assert len(result.questions) == 5


