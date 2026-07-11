import logging
from typing import Dict, Any
from app.agents.state import SimulationState

logger = logging.getLogger(__name__)

DOMAIN_WEIGHTS = {
    "product_manager": {
        "analytical_reasoning": 0.20,
        "ambiguity_tolerance": 0.30,
        "communication_clarity": 0.25,
        "attention_to_detail": 0.10,
        "decisiveness": 0.15
    },
    "sqa_engineer": {
        "analytical_reasoning": 0.20,
        "ambiguity_tolerance": 0.10,
        "communication_clarity": 0.15,
        "attention_to_detail": 0.35,
        "decisiveness": 0.20
    },
    "data_analyst": {
        "analytical_reasoning": 0.35,
        "ambiguity_tolerance": 0.20,
        "communication_clarity": 0.20,
        "attention_to_detail": 0.20,
        "decisiveness": 0.05
    },
    "frontend_engineer": {
        "analytical_reasoning": 0.15,
        "ambiguity_tolerance": 0.20,
        "communication_clarity": 0.20,
        "attention_to_detail": 0.30,
        "decisiveness": 0.15
    },
    "backend_engineer": {
        "analytical_reasoning": 0.30,
        "ambiguity_tolerance": 0.15,
        "communication_clarity": 0.15,
        "attention_to_detail": 0.25,
        "decisiveness": 0.15
    }
}

def _lower_difficulty(current: str) -> str:
    if current == "hard":
        return "medium"
    if current == "medium":
        return "easy"
    return "easy"

def _compute_fit_matrix(history: list) -> Dict[str, float]:
    """
    Calculate the historical baseline running average for each of the 5 core database dimensions
    across all evaluations stored in state['history'].
    """
    all_dims: Dict[str, list] = {
        "analytical_reasoning": [],
        "ambiguity_tolerance": [],
        "communication_clarity": [],
        "attention_to_detail": [],
        "decisiveness": []
    }
    
    for entry in history:
        evaluation = entry.get("evaluation") or {}
        dim_scores = evaluation.get("dimension_scores", {})
        for dim in all_dims.keys():
            if dim in dim_scores:
                all_dims[dim].append(float(dim_scores[dim]))
                
    avg_dims = {
        dim: (sum(vals) / len(vals) if vals else 50.0)
        for dim, vals in all_dims.items()
    }
    
    fit_matrix = {}
    for domain, weights in DOMAIN_WEIGHTS.items():
        weighted_score = sum(avg_dims.get(dim, 50.0) * weight for dim, weight in weights.items())
        fit_matrix[domain] = round(weighted_score, 1)
        
    return fit_matrix

def career_fit_node(state: SimulationState) -> dict:
    """
    Core analytical routing and scoring node.
    Calculates weights, runs the remediation loop engine, and returns state updates.
    """
    current_evaluation = state.get("current_evaluation") or {}
    overall_score = current_evaluation.get("overall_score")
    
    # Fallback to latest_score if overall_score is not inside current_evaluation directly
    if overall_score is None:
        overall_score = state.get("latest_score", 50.0)
        
    is_final = state.get("is_final_scene", False)
    loop_count = state.get("loop_count", 0)
    current_difficulty = state.get("difficulty", "medium")
    history = state.get("history", [])
    
    # Compute the multivariable weighted suitability matrices
    fit_matrix = _compute_fit_matrix(history)
    
    # Automated Remediation Loop Engine
    if overall_score < 40 and not is_final and loop_count < 2:
        should_loop_back = True
        loop_count += 1
        new_difficulty = _lower_difficulty(current_difficulty)
        logger.info(f"career_fit_node → LOOP BACK triggered. Score: {overall_score}. Difficulty {current_difficulty} -> {new_difficulty}")
    else:
        should_loop_back = False
        new_difficulty = current_difficulty
        logger.info(f"career_fit_node → CONTINUE. Score: {overall_score}. Final scene: {is_final}")
        
    update = {
        "should_loop_back": should_loop_back,
        "fit_scores": fit_matrix,
        "career_fit_matrix": fit_matrix
    }
    
    if should_loop_back:
        update["loop_count"] = loop_count
        update["difficulty"] = new_difficulty
        update["lowered_difficulty"] = new_difficulty
    else:
        update["lowered_difficulty"] = None
        
    return update
