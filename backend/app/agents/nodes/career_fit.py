"""
career_fit_node — deterministic fit scoring + feedback loop decision
No LLM. Pure Python.
"""
import logging
from app.agents.state import SimulationState

logger = logging.getLogger(__name__)

DOMAIN_WEIGHTS = {
    "product_manager":      {"analytical_reasoning": 0.20, "ambiguity_tolerance": 0.30, "communication_clarity": 0.25, "attention_to_detail": 0.10, "decisiveness": 0.15},
    "sqa_engineer":         {"analytical_reasoning": 0.20, "ambiguity_tolerance": 0.10, "communication_clarity": 0.15, "attention_to_detail": 0.35, "decisiveness": 0.20},
    "data_analyst":         {"analytical_reasoning": 0.35, "ambiguity_tolerance": 0.20, "communication_clarity": 0.20, "attention_to_detail": 0.20, "decisiveness": 0.05},
    "frontend_engineer":    {"analytical_reasoning": 0.15, "ambiguity_tolerance": 0.20, "communication_clarity": 0.20, "attention_to_detail": 0.30, "decisiveness": 0.15},
    "backend_engineer":     {"analytical_reasoning": 0.30, "ambiguity_tolerance": 0.15, "communication_clarity": 0.15, "attention_to_detail": 0.25, "decisiveness": 0.15},
}

def _lower_difficulty(current: str) -> str:
    if current == "hard":
        return "medium"
    if current == "medium":
        return "easy"
    return "easy"

def _compute_fit_scores(history: list) -> dict:
    """Aggregate dimension scores across all evaluations and compute fit per domain."""
    all_dims: dict[str, list[float]] = {}
    for entry in history:
        evaluation = entry.get("evaluation") or {}
        dim_scores = evaluation.get("dimension_scores", {})
        for dim, val in dim_scores.items():
            if dim not in all_dims:
                all_dims[dim] = []
            all_dims[dim].append(float(val))
    
    avg_dims = {dim: sum(vals)/len(vals) for dim, vals in all_dims.items() if vals}
    
    fit_scores = {}
    for domain, weights in DOMAIN_WEIGHTS.items():
        weighted = sum(avg_dims.get(dim, 50.0) * w for dim, w in weights.items())
        fit_scores[domain] = round(weighted, 1)
    
    return fit_scores

def career_fit_node(state: SimulationState) -> dict:
    """
    Deterministic node. No LLM.
    Decides: continue to report, or loop back to scenario with lower difficulty.
    """
    latest_score = state.get("latest_score", 50.0)
    loop_count = state.get("loop_count", 0)
    is_final = state.get("is_final_scene", False)
    current_difficulty = state.get("difficulty", "medium")
    history = state.get("history", [])
    current_evaluation = state.get("current_evaluation", {})
    
    # Compute fit scores from all history
    fit_scores = _compute_fit_scores(history)
    
    # Decision: loop back if failing, not final, and haven't looped twice
    MAX_LOOPS = 2
    should_loop = (
        latest_score < 40
        and not is_final
        and loop_count < MAX_LOOPS
    )
    
    if should_loop:
        new_difficulty = _lower_difficulty(current_difficulty)
        reasoning = current_evaluation.get("reasoning", "Score below threshold — difficulty reduced.")
        logger.info(f"career_fit_node → LOOP BACK | score: {latest_score} | difficulty: {current_difficulty} → {new_difficulty}")
        return {
            "should_loop_back": True,
            "lowered_difficulty": new_difficulty,
            "difficulty": new_difficulty,
            "loop_count": loop_count + 1,
            "fit_scores": fit_scores,
        }
    
    logger.info(f"career_fit_node → CONTINUE | score: {latest_score} | final: {is_final}")
    return {
        "should_loop_back": False,
        "lowered_difficulty": None,
        "fit_scores": fit_scores,
    }
