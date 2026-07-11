import logging
logger = logging.getLogger(__name__)

from langgraph.graph import StateGraph, START, END
from app.agents.state import SimulationState
from app.agents.nodes.scenario import scenario_node
from app.agents.nodes.evaluation import evaluation_node
from app.agents.nodes.career_fit import career_fit_node
from app.schemas.agent_contracts import (
    EvaluationContext, EvaluationResult,
    FitReportContext, FitReportResult,
    MCQGenerationContext, MCQGenerationResult,
    SceneContent, SceneGenerationContext,
)

# supervisor_node stays inline in graph.py — it's one line
def supervisor_node(state: SimulationState) -> dict:
    domain = state["domain"]
    valid = ["product_manager","sqa_engineer","data_analyst","frontend_engineer","backend_engineer"]
    if domain not in valid:
        raise ValueError(f"Unknown domain: {domain}")
    return {"active_domain": domain}

def report_node(state: SimulationState) -> dict:
    # TODO Shayan builds this — stub for now
    return {"report": {"status": "report_generation_pending"}}

def route_after_career_fit(state: SimulationState):
    if state.get("should_loop_back"):
        return "scenario_node"
    elif state.get("is_final_scene"):
        return "report_node"
    else:
        return END

# TWO SEPARATE GRAPHS:
# 1. scene_graph — invoked by generate_scene()
# 2. eval_graph  — invoked by evaluate_response()
# This is because LangGraph needs a clean entry point per call type.

# Scene generation graph
scene_builder = StateGraph(SimulationState)
scene_builder.add_node("supervisor_node", supervisor_node)
scene_builder.add_node("scenario_node", scenario_node)
scene_builder.add_edge(START, "supervisor_node")
scene_builder.add_edge("supervisor_node", "scenario_node")
scene_builder.add_edge("scenario_node", END)

# Evaluation graph (includes feedback loop)
eval_builder = StateGraph(SimulationState)
eval_builder.add_node("evaluation_node", evaluation_node)
eval_builder.add_node("career_fit_node", career_fit_node)
eval_builder.add_node("scenario_node", scenario_node)
eval_builder.add_node("report_node", report_node)
eval_builder.add_edge(START, "evaluation_node")
eval_builder.add_edge("evaluation_node", "career_fit_node")
eval_builder.add_conditional_edges(
    "career_fit_node",
    route_after_career_fit,
    {
        "scenario_node": "scenario_node",
        "report_node": "report_node",
        END: END,
    }
)
eval_builder.add_edge("scenario_node", END)
eval_builder.add_edge("report_node", END)

# CHECKPOINTER setup
def get_checkpointer():
    from app.core.config import get_settings
    settings = get_settings()
    from langgraph.checkpoint.postgres import PostgresSaver
    # Handle settings.database_url which might be a MultiHostUrl
    db_url = str(settings.database_url)
    return PostgresSaver.from_conn_string(db_url)

try:
    checkpointer = get_checkpointer()
    checkpointer.setup() # Initialize tables if they don't exist
except Exception as e:
    logger.warning(f"PostgresCheckpointer unavailable: {e} — using MemorySaver")
    from langgraph.checkpoint.memory import MemorySaver
    checkpointer = MemorySaver()

scene_graph = scene_builder.compile(checkpointer=checkpointer)
eval_graph = eval_builder.compile(checkpointer=checkpointer)

# --- Entry points called by agent_client.py ---

def run_scenario_step(ctx: SceneGenerationContext) -> SceneContent:
    """Convert SceneGenerationContext to SimulationState and run scene graph."""
    state = {
        "simulation_session_id": ctx.simulation_session_id,
        "user_id": ctx.user_id,
        "domain": ctx.domain,
        "difficulty": ctx.difficulty,
        "scene_number": ctx.scene_number,
        "user_profile": {
            "self_rating": ctx.user_profile_snippet.self_rating,
            "core_interests": ctx.user_profile_snippet.core_interests,
        },
        "history": [
            {"scene": h.scene.model_dump(), "evaluation": h.evaluation.model_dump()}
            for h in (ctx.history or [])
        ],
        # Defaults
        "active_domain": ctx.domain,
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
    }
    config = {"configurable": {"thread_id": ctx.simulation_session_id}}
    result = scene_graph.invoke(state, config=config)
    scene_dict = result.get("current_scene", {})
    # Convert dict to SceneContent
    return SceneContent(**scene_dict)

def run_evaluation_step(ctx: EvaluationContext) -> EvaluationResult:
    """Convert EvaluationContext to SimulationState and run eval graph."""
    state = {
        "simulation_session_id": ctx.simulation_session_id,
        "user_id": ctx.user_id,
        "domain": ctx.domain,
        "difficulty": ctx.difficulty,
        "scene_number": ctx.scene_number,
        "user_profile": {},
        "history": [
            {"scene": h.scene.model_dump(), "evaluation": h.evaluation.model_dump()}
            for h in (ctx.history or [])
        ],
        "current_scene": ctx.scene_content.model_dump(),
        "student_response": ctx.user_response.raw_text or "",
        # Defaults
        "active_domain": ctx.domain,
        "current_evaluation": None,
        "latest_score": 0.0,
        "should_loop_back": False,
        "lowered_difficulty": None,
        "fit_scores": None,
        "report": None,
        "is_final_scene": ctx.scene_content.is_final_scene,
        "loop_count": 0,
    }
    config = {"configurable": {"thread_id": ctx.simulation_session_id}}
    result = eval_graph.invoke(state, config=config)
    evaluation_dict = result.get("current_evaluation", {})
    return EvaluationResult(**evaluation_dict)

def run_fit_report_step(ctx: FitReportContext) -> FitReportResult:
    raise NotImplementedError("Shayan builds this — report_node")

def run_mcq_generation_step(ctx: MCQGenerationContext) -> MCQGenerationResult:
    raise NotImplementedError("Ayesha builds this next")
