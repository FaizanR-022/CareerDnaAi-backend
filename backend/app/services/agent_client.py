import asyncio
import logging
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

logger = logging.getLogger(__name__)

async def generate_scene(ctx: SceneGenerationContext) -> SceneContent:
    if get_settings().agent_layer_impl == "mock":
        return await asyncio.to_thread(mock_agent.generate_scene, ctx)
    from app.agents.graph import run_scenario_step
    return await run_scenario_step(ctx)

async def evaluate_response(ctx: EvaluationContext) -> EvaluationResult:
    if get_settings().agent_layer_impl == "mock":
        return await asyncio.to_thread(mock_agent.evaluate_response, ctx)
    from app.agents.graph import run_evaluation_step
    return await run_evaluation_step(ctx)

async def generate_fit_report(ctx: FitReportContext) -> FitReportResult:
    if get_settings().agent_layer_impl == "mock":
        return await asyncio.to_thread(mock_agent.generate_fit_report, ctx)
    from app.agents.graph import run_fit_report_step
    return await run_fit_report_step(ctx)

async def generate_mcqs(ctx: MCQGenerationContext) -> MCQGenerationResult:
    if get_settings().agent_layer_impl == "mock":
        return await asyncio.to_thread(mock_agent.generate_mcqs, ctx)
    from app.agents.graph import run_mcq_generation_step
    return await run_mcq_generation_step(ctx)
