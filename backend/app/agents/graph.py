from langgraph.graph import StateGraph, START, END

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
from app.agents.state import SimulationState

# --- Node Stubs ---
def supervisor_node(state: SimulationState) -> dict:
    domain = state["domain"]
    valid = ["product_manager", "sqa_engineer", "data_analyst", "frontend_engineer", "backend_engineer"]
    if domain not in valid:
        raise ValueError(f"Unknown domain: {domain}")
    return {"active_domain": domain}

def scenario_node(state: SimulationState) -> dict:
    # TODO: Implement LLM scene generation
    pass

def evaluation_node(state: SimulationState) -> dict:
    # TODO: Implement LLM-as-judge scoring
    pass

def career_fit_node(state: SimulationState) -> dict:
    # TODO: Implement deterministic fit scoring + loop logic
    pass

def report_node(state: SimulationState) -> dict:
    # TODO: Implement LLM narrative generation
    pass

# --- Routing Logic ---
def route_after_career_fit(state: SimulationState):
    if state.get("should_loop_back"):
        return "scenario_node"
    elif state.get("is_final_scene"):
        return "report_node"
    else:
        return END

# --- Graph Definition ---
builder = StateGraph(SimulationState)

builder.add_node("supervisor_node", supervisor_node)
builder.add_node("scenario_node", scenario_node)
builder.add_node("evaluation_node", evaluation_node)
builder.add_node("career_fit_node", career_fit_node)
builder.add_node("report_node", report_node)

# We will configure entry points and edges later based on the workflow state
# builder.add_edge(START, "supervisor_node")
# ...

# compiled_graph = builder.compile()

# --- Agent Client Entry Points ---

def run_scenario_step(ctx: SceneGenerationContext) -> SceneContent:
    raise NotImplementedError("Graph scenario step not fully implemented yet")

def run_evaluation_step(ctx: EvaluationContext) -> EvaluationResult:
    raise NotImplementedError("Graph evaluation step not fully implemented yet")

def run_fit_report_step(ctx: FitReportContext) -> FitReportResult:
    raise NotImplementedError("Graph fit report step not fully implemented yet")

def run_mcq_generation_step(ctx: MCQGenerationContext) -> MCQGenerationResult:
    raise NotImplementedError("Graph MCQ generation step not fully implemented yet")
