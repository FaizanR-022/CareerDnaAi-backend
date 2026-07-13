from typing import Optional, Literal
from typing_extensions import TypedDict

class SimulationState(TypedDict):
    # From backend context
    simulation_session_id: str
    user_id: str
    domain: str          # "product_manager" | "sqa_engineer" | etc.
    difficulty: str      # "easy" | "medium" | "hard"
    scene_number: int
    user_profile: dict   # {self_rating, core_interests}
    history: list        # list of {scene, evaluation} dicts

    # Set by supervisor_node
    active_domain: str

    # Set by scenario_node
    current_scene: Optional[dict]     # SceneContent as dict

    # Set by evaluation_node
    current_evaluation: Optional[dict]  # EvaluationResult as dict
    latest_score: float

    # Set by career_fit_node
    should_loop_back: bool
    lowered_difficulty: Optional[str]
    fit_scores: Optional[dict]

    # Set by report_node (only on final)
    report: Optional[dict]

    # Graph control
    is_final_scene: bool
    loop_count: int      # prevent infinite loops
    student_response: str

    # NPC trust scores — keyed by npc_id (e.g. "dan_frontend_dev")
    # Updated by evaluation_node trust modifier logic
    npc_trust: Optional[dict]

