from app.agents.domains.base_agent import BaseDomainAgent

class DAAgent(BaseDomainAgent):
    domain = "da"
    
    def generate_scene(self, session_context, difficulty, scene_number):
        return {
            "scene_type": "data_analysis",
            "scene_number": scene_number,
            "title": "DA Scene (coming soon)",
            "description": "DA simulation scene — agent implementation in progress.",
            "active_npc": "dan_frontend_dev",
            "npc_opening_messages": [],
            "workspace_data": {},
            "branch_point": {"good_signals": [], "bad_signals": [], "dimensions": []},
            "difficulty_modifiers": {},
            "is_final_scene": scene_number >= 4
        }
    
    def evaluate_response(self, scene, student_response, session_context):
        return {
            "overall_score": 60, "dimension_scores": {},
            "behavioural_flags": [], "justification": "DA evaluation coming soon.",
            "should_lower_difficulty": False
        }
    
    def get_npc_response(self, npc_id, student_message, session_context, hard_constraints):
        return {
            "dialogue": "Noted. Let me review that.",
            "updated_npc_memory": {}, "sentiment_signal": "neutral", "trust_delta": 0
        }
