from app.core.config import get_settings
from app.schemas.agent_contracts import (
    EvaluationContext,
    EvaluationResult,
    FitReportContext,
    FitReportResult,
    MCQGenerationContext,
    MCQGenerationResult,
    SceneContent,
    SceneGenerationContext,
)
from app.services import mock_agent


def generate_scene(ctx: SceneGenerationContext) -> SceneContent:
    if get_settings().agent_layer_impl == "mock":
        return mock_agent.generate_scene(ctx)
    raise NotImplementedError("Real agent layer scene generation is not wired up yet")


def evaluate_response(ctx: EvaluationContext) -> EvaluationResult:
    if get_settings().agent_layer_impl == "mock":
        return mock_agent.evaluate_response(ctx)
    raise NotImplementedError("Real agent layer response evaluation is not wired up yet")


def generate_fit_report(ctx: FitReportContext) -> FitReportResult:
    if get_settings().agent_layer_impl == "mock":
        return mock_agent.generate_fit_report(ctx)
    raise NotImplementedError("Real agent layer fit report generation is not wired up yet")


def generate_mcqs(ctx: MCQGenerationContext) -> MCQGenerationResult:
    if get_settings().agent_layer_impl == "mock":
        return mock_agent.generate_mcqs(ctx)
    raise NotImplementedError("Real agent layer MCQ generation is not wired up yet")
