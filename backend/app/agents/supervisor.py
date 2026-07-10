import logging
from app.agents.domains.pm_agent import PMAgent
from app.agents.domains.sqa_agent import SQAAgent
from app.agents.domains.da_agent import DAAgent
from app.agents.domains.fe_agent import FEAgent
from app.agents.domains.be_agent import BEAgent
from app.agents.domains.base_agent import BaseDomainAgent

logger = logging.getLogger(__name__)

DOMAIN_AGENTS: dict[str, BaseDomainAgent] = {
    "pm":  PMAgent(),
    "sqa": SQAAgent(),
    "da":  DAAgent(),
    "fe":  FEAgent(),
    "be":  BEAgent(),
}

def get_domain_agent(domain: str) -> BaseDomainAgent:
    """
    Routes to the correct domain agent.
    No LLM — pure deterministic routing.
    Raises ValueError if domain unknown.
    """
    agent = DOMAIN_AGENTS.get(domain)
    if not agent:
        raise ValueError(
            f"Unknown domain: {domain}. "
            f"Valid: {list(DOMAIN_AGENTS.keys())}"
        )
    logger.info(f"Supervisor routed to {domain} agent")
    return agent

def run_simulation_step(
    domain: str,
    action: str,
    session_context: dict,
    student_input: Optional[str] = None,
    scene: Optional[dict] = None,
) -> dict:
    """
    Main entry point called by session_service.
    
    action: "generate_scene" | "evaluate_response" | "npc_response"
    
    Returns whatever the domain agent returns for that action.
    """
    from typing import Optional
    agent = get_domain_agent(domain)
    
    if action == "generate_scene":
        scene_number = len(session_context.get("scenes_completed", [])) + 1
        difficulty = session_context.get("difficulty", "medium")
        
        # Rule-based difficulty adjustment — no LLM, no Difficulty Agent
        if agent.should_lower_difficulty(session_context):
            if difficulty == "hard":
                difficulty = "medium"
            elif difficulty == "medium":
                difficulty = "easy"
            logger.info(f"Difficulty lowered to {difficulty} — student struggling")
        
        result = agent.generate_scene(session_context, difficulty, scene_number)
        result["is_complete"] = agent.is_simulation_complete(session_context)
        return result
    
    elif action == "evaluate_response":
        return agent.evaluate_response(scene, student_input, session_context)
    
    elif action == "npc_response":
        npc_id = session_context.get("active_npc_id", "sara_khan")
        hard_constraints = session_context.get("hard_constraints", {})
        return agent.get_npc_response(
            npc_id, student_input, session_context, hard_constraints
        )
    
    else:
        raise ValueError(f"Unknown action: {action}")
