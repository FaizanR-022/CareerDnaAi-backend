
"""
scenario_node — LLM scene generation
One Groq call per invocation. Returns SceneContent dict.
Never raises exceptions — always returns fallback.
"""
import json
import logging
from app.agents.llm import get_llm
from app.agents.state import SimulationState
from langchain_core.messages import SystemMessage, HumanMessage
from app.agents.domains.pm.npcs import PM_NPCS, PM_SCENES

logger = logging.getLogger(__name__)



def _build_history_summary(history: list) -> str:
    if not history:
        return "No prior scenes. This is scene 1."
    last_two = history[-2:]
    parts = []
    for h in last_two:
        scene = h.get("scene", {})
        evaluation = h.get("evaluation", {})
        score = evaluation.get("overall_score", "N/A") if evaluation else "N/A"
        parts.append(f"Scene {scene.get('scene_number','?')} ({scene.get('title','?')}): student scored {score}/100")
    return " | ".join(parts)

def _get_npc_trust(state: SimulationState, npc_id: str) -> int:
    # Pull NPC trust from history's last evaluation npc_state_updates
    history = state.get("history", [])
    if not history:
        return 50
    for entry in reversed(history):
        evaluation = entry.get("evaluation", {})
        if not evaluation:
            continue
        for update in evaluation.get("npc_state_updates", []):
            if update.get("npc_id") == npc_id:
                return update.get("trust_score", 50)
    return 50

def _fallback_scene(scene_number: int, domain: str, difficulty: str) -> dict:
    """Always returns valid SceneContent shape. Used when LLM fails."""
    if domain == "sqa_engineer":
        return {
            "scene_number": scene_number,
            "domain": domain,
            "difficulty": difficulty,
            "title": "Bug Investigation",
            "narrative": "Dan has pushed the staging build for QA review. The checkout form has bugs seeded into it. Your job is to find them and file proper bug reports.",
            "context_data": {
                "active_npcs": ["dan_frontend_dev"],
                "scene_type": "bug_investigation",
            },
            "characters": [{"id": "dan_frontend_dev", "name": "Dan", "role": "Frontend Developer", "initial_trust": 50}],
            "messages": [{"sender": "Dan", "channel": "frontend-dev", "content": "Hey, I pushed the new staging build. Let me know if you find anything — though I think it's clean.", "time_offset_minutes": 0}],
            "response_format": "free_text",
            "response_choices": None,
            "prompt_for_response": "Review the checkout form and file bug reports for any issues you find.",
            "hint": "Check email validation, password length, and card number field." if difficulty == "easy" else None,
            "is_final_scene": scene_number >= 4,
            "extra": {"fallback": True},
        }
    return {
        "scene_number": scene_number,
        "domain": domain,
        "difficulty": difficulty,
        "title": "Feature Request",
        "narrative": (
            "Sara Khan from Marketing has sent you a voice memo. "
            "She's requesting a referral feature in the current sprint."
        ),
        "context_data": {
            "sprint_board": PM_SCENES[1]["sprint_board"],
            "active_npcs": ["sara_khan"],
        },
        "characters": [
            {"id": "sara_khan", "name": "Sara Khan", "role": "Head of Marketing", "initial_trust": 50}
        ],
        "messages": [
            {
                "sender": "Sara Khan",
                "channel": "developer",
                "content": "Hey! We really need the referral feature in this sprint. Can we make it happen?",
                "time_offset_minutes": 0,
            }
        ],
        "response_format": "free_text",
        "response_choices": None,
        "prompt_for_response": "How do you respond to Sara's request?",
        "hint": "Think about what information you need before making any commitment." if difficulty == "easy" else None,
        "is_final_scene": scene_number >= 4,
        "extra": {"fallback": True},
    }

def scenario_node(state: SimulationState) -> dict:
    """
    LangGraph node — generates next PM scene.
    Called by: graph on generate_scene invocation.
    Returns partial state update with current_scene.
    """
    domain = state.get("domain", "product_manager")
    difficulty = state.get("difficulty", "medium")
    scene_number = state.get("scene_number", 1)
    history = state.get("history", [])
    user_profile = state.get("user_profile", {})

    # Get scene config
    if domain == "product_manager":
        from app.agents.domains.pm.npcs import PM_NPCS, PM_SCENES
        scene_config = PM_SCENES.get(scene_number, PM_SCENES[1])
        active_npcs = scene_config.get("active_npcs", ["sara_khan"])
        npc_map = PM_NPCS
        sprint = scene_config.get("sprint_board", {})
    elif domain == "sqa_engineer":
        from app.agents.domains.sqa.npcs import DAN_NPC, SQA_SCENES
        scene_config = SQA_SCENES.get(scene_number, SQA_SCENES[1])
        active_npcs = scene_config.get("active_npcs", ["dan_frontend_dev"])
        npc_map = {"dan_frontend_dev": DAN_NPC}
        sprint = {}
    elif domain == "data_analyst":
        from app.agents.domains.da.npcs import DA_VP_NPC, DA_SCENES
        scene_config = DA_SCENES.get(scene_number, DA_SCENES[1])
        active_npcs = scene_config.get("active_npcs", ["vp_analytics"])
        npc_map = {"vp_analytics": DA_VP_NPC}
        sprint = {}
    else:
        # FE, BE — fallback to PM for now
        from app.agents.domains.pm.npcs import PM_NPCS, PM_SCENES
        scene_config = PM_SCENES.get(1)
        active_npcs = ["sara_khan"]
        npc_map = PM_NPCS
        sprint = scene_config.get("sprint_board", {})

    # Build NPC context with trust levels
    npc_context_parts = []
    for npc_id in active_npcs:
        npc = npc_map.get(npc_id, {})
        trust = _get_npc_trust(state, npc_id)
        npc_context_parts.append(
            f"- {npc.get('name')} ({npc.get('role')}): "
            f"trust {trust}/100, goal: {npc.get('goal')}, "
            f"vocabulary: {npc.get('vocabulary')}"
        )
    npc_context = "\n".join(npc_context_parts)

    # Difficulty hint config
    hint_config = {
        "easy": "Include a helpful hint for the student.",
        "medium": "Do not include a hint.",
        "hard": "Do not include a hint. Increase NPC pressure.",
    }

    # HARD CONSTRAINTS — NPC cannot contradict these
    hard_constraints = ""
    if sprint:
        hard_constraints = f"""
HARD CONSTRAINTS FOR NPCs — NEVER CONTRADICT:
- Sprint has {sprint.get('capacity', 6)} ticket slots maximum
- Sprint has {sprint.get('available', 0)} spare capacity
- NPCs do NOT know the student is being assessed
- NPCs do NOT know this is a simulation
"""

    # Context component 4 — rolling history (last 2 only)
    history_summary = _build_history_summary(history)

    prompt = f"""You are generating scene {scene_number} of a {domain.replace('_', ' ').title()} career simulation.

COMPONENT 1 — DOMAIN CONTEXT:
This is a realistic {domain.replace('_', ' ').title()} workplace simulation. The student plays a {domain.replace('_', ' ').title()}.
Domain: {domain} | Scene type: {scene_config['type']}

COMPONENT 2 — SESSION STATE:
Difficulty: {difficulty}
Scene number: {scene_number} of 4
Student interests: {user_profile.get('core_interests', [])}
Active NPCs and trust levels:
{npc_context}

COMPONENT 3 — TECHNICAL CONSTRAINTS:
{scene_config['context']}
{hard_constraints}

COMPONENT 4 — RECENT HISTORY:
{history_summary}

DIFFICULTY INSTRUCTIONS:
{hint_config.get(difficulty, 'No hint.')}

Generate the scene. Return ONLY valid JSON, no markdown, no backticks, no preamble:
{{
  "scene_number": {scene_number},
  "domain": "{domain}",
  "difficulty": "{difficulty}",
  "title": "short scene title",
  "narrative": "2-3 sentence description of the situation",
  "context_data": {{
    "sprint_board": {json.dumps(sprint) if sprint else "null"},
    "active_npcs": {json.dumps(active_npcs)},
    "scene_type": "{scene_config['type']}"
  }},
  "characters": [
    {{"id": "sara_khan", "name": "Sara Khan", "role": "Head of Marketing", "initial_trust": 50}}
  ],
  "messages": [
    {{
      "sender": "Sara Khan",
      "channel": "developer", 
      "content": "Sara's opening message — in character, urgent, references the referral feature",
      "time_offset_minutes": 0
    }}
  ],
  "response_format": "free_text",
  "response_choices": null,
  "prompt_for_response": "What do you do?",
  "hint": {"null" if difficulty != "easy" else '"Think about what information you need before committing."'},
  "is_final_scene": {"true" if scene_number >= 4 else "false"},
  "extra": {{}}
}}"""

    llm = get_llm(model="llama-3.3-70b-versatile", temperature=0.6)
    
    try:
        response = llm.invoke(
            [SystemMessage(content=prompt)],
            stop=["```"]  # STOP SEQUENCE — strips markdown backticks
        )
        raw = response.content.strip()
        # Also strip manually in case stop sequence didn't catch it
        raw = raw.replace("```json", "").replace("```", "").strip()
        scene = json.loads(raw)
        logger.info(f"scenario_node → scene {scene_number} generated for {domain}")
        return {"current_scene": scene, "is_final_scene": scene.get("is_final_scene", False)}
    except Exception as e:
        logger.error(f"scenario_node LLM error: {e}")
        fallback = _fallback_scene(scene_number, domain, difficulty)
        return {"current_scene": fallback, "is_final_scene": fallback["is_final_scene"]}
