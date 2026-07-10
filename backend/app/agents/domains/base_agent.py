from abc import ABC, abstractmethod
from typing import Optional

class BaseDomainAgent(ABC):
    """
    Contract every domain agent must implement.
    No LLM calls here — just the interface definition.
    """
    
    domain: str = ""  # override in subclass: "pm", "sqa", etc.
    
    @abstractmethod
    def generate_scene(
        self,
        session_context: dict,
        difficulty: str,
        scene_number: int
    ) -> dict:
        """
        Generate the next simulation scene.
        
        session_context contains:
          - user_profile: dict (name, interests, self_ratings)
          - difficulty: str (easy/medium/hard)
          - scenes_completed: list of previous scenes + evaluations
          - npc_states: current trust/memory per NPC
          - scores: running dimension scores
        
        Returns:
          - scene_id: str
          - scene_type: str (e.g. "stakeholder_request", "sprint_conflict")
          - title: str
          - description: str (shown to student)
          - npc_messages: list of opening NPC messages
          - workspace_data: dict (sprint board, PRD, etc. — domain specific)
          - is_final_scene: bool
          - difficulty_modifiers: dict
        """
        raise NotImplementedError
    
    @abstractmethod
    def evaluate_response(
        self,
        scene: dict,
        student_response: str,
        session_context: dict
    ) -> dict:
        """
        Score the student's response to a scene.
        
        Returns:
          - overall_score: int (0-100)
          - dimension_scores: dict (5 dimensions, 0-100 each)
          - behavioural_flags: list[str]
          - justification: str (1 sentence)
          - should_lower_difficulty: bool (True if student struggling)
        """
        raise NotImplementedError
    
    @abstractmethod
    def get_npc_response(
        self,
        npc_id: str,
        student_message: str,
        session_context: dict,
        hard_constraints: dict
    ) -> dict:
        """
        Generate NPC dialogue for a student message.
        
        hard_constraints: facts NPC cannot contradict
          e.g. {"sprint_capacity": 0, "is_simulation": False}
        
        Returns:
          - dialogue: str
          - updated_npc_memory: dict
          - sentiment_signal: str (positive/neutral/negative)
          - trust_delta: int
        """
        raise NotImplementedError
    
    def is_simulation_complete(
        self,
        session_context: dict,
        max_scenes: int = 4
    ) -> bool:
        """
        Default: complete when max_scenes reached.
        Override in domain agent if different logic needed.
        """
        return len(session_context.get("scenes_completed", [])) >= max_scenes
    
    def should_lower_difficulty(
        self,
        session_context: dict,
        failing_threshold: float = 40.0
    ) -> bool:
        """
        Rule-based difficulty adjustment — no LLM.
        If avg score below threshold for last 2 scenes, lower difficulty.
        """
        scores = session_context.get("scores", {})
        if not scores:
            return False
        avg = sum(v for v in scores.values() if v > 0) / max(
            1, sum(1 for v in scores.values() if v > 0)
        )
        return avg < failing_threshold
