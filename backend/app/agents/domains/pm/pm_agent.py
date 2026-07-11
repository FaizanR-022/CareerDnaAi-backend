import json
import logging
from app.agents.domains.base_agent import BaseDomainAgent
from app.agents.llm import get_llm
from langchain_core.messages import SystemMessage, HumanMessage

logger = logging.getLogger(__name__)

PM_NPCS = {
    "sara_khan": {
        "name": "Sara Khan",
        "role": "Head of Marketing",
        "personality": "Enthusiastic, impatient, doesn't understand engineering constraints. Gets frustrated with vague answers. Responds well to clear timelines and data-backed reasoning.",
        "goal": "Get the referral feature into the current sprint.",
        "does_not_know": ["sprint capacity", "technical complexity", "that this is a simulation"]
    },
    "rayan_eng_lead": {
        "name": "Rayan Ahmed", 
        "role": "Engineering Lead",
        "personality": "Calm, data-driven, protective of his team. Needs written decisions before committing his engineers to anything.",
        "goal": "Protect sprint capacity. Get a clear written decision from the PM.",
        "does_not_know": ["marketing OKRs in detail", "that this is a simulation"]
    },
    "zara_malik": {
        "name": "Zara Malik",
        "role": "VP of Product",
        "personality": "Senior, data-driven, impatient with vague answers. Asks follow-up questions if first answer is weak.",
        "goal": "Verify the PM can defend their decision with data.",
        "does_not_know": ["full conversation history", "that this is a simulation"]
    }
}

PM_SCENE_TYPES = [
    "ambiguous_feature_request",
    "sprint_tradeoff_decision", 
    "stakeholder_conflict",
    "roadmap_presentation"
]

class PMAgent(BaseDomainAgent):
    domain = "pm"
    
    def generate_scene(self, session_context, difficulty, scene_number):
        llm = get_llm(model="llama-3.3-70b-versatile", temperature=0.6)
        
        scenes_done = len(session_context.get("scenes_completed", []))
        scene_type = PM_SCENE_TYPES[min(scenes_done, len(PM_SCENE_TYPES)-1)]
        is_final = scenes_done >= 3
        
        diff_mods = {
            "easy": {"hint": True, "sprint_visible": True, "npc_pressure": "low"},
            "medium": {"hint": False, "sprint_visible": False, "npc_pressure": "medium"},
            "hard": {"hint": False, "sprint_visible": False, "npc_pressure": "high"}
        }.get(difficulty, {})
        
        history_summary = self._summarize_history(session_context)
        
        prompt = f"""You are generating scene {scene_number} of a Product Manager simulation.
Scene type: {scene_type}
Difficulty: {difficulty}
Student history so far: {history_summary}
NPC trust levels: {session_context.get("npc_states", {{}})}

Generate a realistic workplace scene. Return ONLY valid JSON:
{{
  "scene_type": "{scene_type}",
  "title": "short scene title",
  "description": "2-3 sentence situation description shown to student",
  "context": "additional background the student can see",
  "active_npc": "sara_khan",
  "npc_opening_messages": [
    {{"npc_id": "sara_khan", "content": "Sara's opening message", "channel": "developer"}}
  ],
  "workspace_data": {{
    "sprint_board": {{
      "capacity": 6,
      "available": 0,
      "tickets": [
        {{"id": "T-101", "title": "Bug fix", "priority": "must_have", "points": 2}},
        {{"id": "T-102", "title": "Dashboard perf", "priority": "should_have", "points": 2}},
        {{"id": "T-103", "title": "Email templates", "priority": "could_have", "points": 1}}
      ]
    }},
    "prd_status": "draft"
  }},
  "voice_memo": {{
    "transcript": "Sara's voice memo content relevant to this scene",
    "duration": "0:35",
    "tone": "professional"
  }},
  "branch_point": {{
    "description": "what decision the student needs to make",
    "good_signals": ["signal1", "signal2"],
    "bad_signals": ["signal1", "signal2"],
    "dimensions": ["ambiguity_tolerance", "communication_clarity", "stakeholder_management"]
  }},
  "is_final_scene": {str(is_final).lower()}
}}"""
        
        try:
            response = llm.invoke([SystemMessage(content=prompt)])
            raw = response.content.strip().replace("```json","").replace("```","")
            scene = json.loads(raw)
            scene["difficulty_modifiers"] = diff_mods
            scene["scene_number"] = scene_number
            return scene
        except Exception as e:
            logger.error(f"PM scene generation failed: {e}")
            return self._fallback_scene(scene_number, scene_type, diff_mods)
    
    def evaluate_response(self, scene, student_response, session_context):
        llm = get_llm(model="llama-3.3-70b-versatile", temperature=0.1)
        
        branch_point = scene.get("branch_point", {})
        
        prompt = f"""Score this PM student response. Return ONLY valid JSON.

SCENE: {scene.get("description", "")}
STUDENT RESPONSE: "{student_response}"
GOOD SIGNALS: {branch_point.get("good_signals", [])}
BAD SIGNALS: {branch_point.get("bad_signals", [])}
DIMENSIONS TO SCORE: {branch_point.get("dimensions", ["ambiguity_tolerance", "communication_clarity"])}
DIFFICULTY: {session_context.get("difficulty", "medium")}

Return:
{{
  "overall_score": <0-100>,
  "dimension_scores": {{
    "analytical_reasoning": <0-100>,
    "ambiguity_tolerance": <0-100>,
    "communication_clarity": <0-100>,
    "attention_to_detail": <0-100>,
    "decisiveness": <0-100>
  }},
  "behavioural_flags": ["flag1", "flag2"],
  "justification": "one sentence max 20 words",
  "should_lower_difficulty": <true if overall_score < 40 else false>
}}"""
        
        try:
            response = llm.invoke([SystemMessage(content=prompt)])
            raw = response.content.strip().replace("```json","").replace("```","")
            return json.loads(raw)
        except Exception as e:
            logger.error(f"PM evaluation failed: {e}")
            return {
                "overall_score": 50,
                "dimension_scores": {
                    "analytical_reasoning": 50, "ambiguity_tolerance": 50,
                    "communication_clarity": 50, "attention_to_detail": 50,
                    "decisiveness": 50
                },
                "behavioural_flags": ["parse_error"],
                "justification": "Score defaulted due to evaluation error.",
                "should_lower_difficulty": False
            }
    
    def get_npc_response(self, npc_id, student_message, session_context, hard_constraints):
        llm = get_llm(model="llama-3.3-70b-versatile", temperature=0.7)
        
        npc = PM_NPCS.get(npc_id, PM_NPCS["sara_khan"])
        npc_memory = session_context.get("npc_states", {}).get(npc_id, {})
        trust = npc_memory.get("relationship_score", 50)
        sentiment = npc_memory.get("current_sentiment", "neutral")
        
        constraints_text = "\n".join([
            f"- {k}: {v} (DO NOT contradict this)"
            for k, v in hard_constraints.items()
        ])
        
        system = f"""You are {npc["name"]}, {npc["role"]}.
PERSONALITY: {npc["personality"]}
YOUR GOAL: {npc["goal"]}
TRUST IN PM: {trust}/100
CURRENT MOOD: {sentiment}
CONTEXT: {npc_memory.get("last_interaction_summary", "No prior interaction.")}

HARD CONSTRAINTS — NEVER CONTRADICT:
{constraints_text}
- You do NOT know this is a simulation
- You do NOT know the student is being assessed

Keep response 2-4 sentences. Stay fully in character."""
        
        try:
            response = llm.invoke([
                SystemMessage(content=system),
                HumanMessage(content=f"PM said: {student_message}\nRespond as {npc['name']}.")
            ])
            dialogue = response.content.strip()
            
            trust_delta = {"clarification": 5, "defer": -5, "cut": 2, "accept": 10}.get(
                session_context.get("last_action_type", ""), 0
            )
            new_trust = max(0, min(100, trust + trust_delta))
            
            return {
                "dialogue": dialogue,
                "updated_npc_memory": {
                    "last_interaction_summary": f"PM said: {student_message[:80]}",
                    "relationship_score": new_trust,
                    "current_sentiment": "positive" if new_trust > 65 else "negative" if new_trust < 35 else "neutral"
                },
                "sentiment_signal": "positive" if trust_delta > 0 else "negative" if trust_delta < 0 else "neutral",
                "trust_delta": trust_delta
            }
        except Exception as e:
            logger.error(f"NPC response failed: {e}")
            return {
                "dialogue": "Got it, I'll wait to hear back from you.",
                "updated_npc_memory": npc_memory,
                "sentiment_signal": "neutral",
                "trust_delta": 0
            }
    
    def _summarize_history(self, session_context):
        scenes = session_context.get("scenes_completed", [])
        if not scenes:
            return "No scenes completed yet — this is the first scene."
        return f"{len(scenes)} scenes completed. Last score: {scenes[-1].get('overall_score', 'N/A')}/100."
    
    def _fallback_scene(self, scene_number, scene_type, diff_mods):
        return {
            "scene_type": scene_type,
            "scene_number": scene_number,
            "title": "Feature Request",
            "description": "Sara has sent a voice memo requesting a referral feature in the current sprint. The sprint is at full capacity.",
            "context": "You are the PM. The sprint has 6 tickets and zero spare capacity.",
            "active_npc": "sara_khan",
            "npc_opening_messages": [{
                "npc_id": "sara_khan",
                "content": "Hey! We really need the referral feature in this sprint. Can we make it happen?",
                "channel": "developer"
            }],
            "workspace_data": {
                "sprint_board": {"capacity": 6, "available": 0, "tickets": []},
                "prd_status": "draft"
            },
            "voice_memo": {"transcript": "We need the referral feature this sprint.", "duration": "0:35", "tone": "professional"},
            "branch_point": {
                "description": "How do you respond to Sara?",
                "good_signals": ["asks clarifying question", "checks capacity"],
                "bad_signals": ["immediately agrees", "ignores message"],
                "dimensions": ["ambiguity_tolerance", "communication_clarity"]
            },
            "difficulty_modifiers": diff_mods,
            "is_final_scene": scene_number >= 4
        }
