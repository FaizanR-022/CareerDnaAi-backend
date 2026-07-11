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

def run_scenario_step(ctx: SceneGenerationContext) -> SceneContent:
    raise NotImplementedError("Graph scenario step not implemented yet")

def run_evaluation_step(ctx: EvaluationContext) -> EvaluationResult:
    raise NotImplementedError("Graph evaluation step not implemented yet")

def run_fit_report_step(ctx: FitReportContext) -> FitReportResult:
    raise NotImplementedError("Graph fit report step not implemented yet")

def run_mcq_generation_step(ctx: MCQGenerationContext) -> MCQGenerationResult:
    raise NotImplementedError("Graph MCQ generation step not implemented yet")
