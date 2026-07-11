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

logger = logging.getLogger(__name__)

# PM NPC PERSONAS — hard constraints enforced
PM_NPCS = {
    "sara_khan": {
        "name": "Sara Khan",
        "role": "Head of Marketing",
        "personality": (
            "Enthusiastic, impatient, driven by growth metrics. "
            "Doesn't understand engineering constraints or sprint capacity. "
            "Responds well to data and clear timelines. "
            "Gets frustrated with vague answers. Never mentions code."
        ),
        "goal": "Get the referral feature into the current sprint.",
        "vocabulary": "OKRs, growth metrics, CAC, referral features, viral loops, conversion funnels",
        "never_says": "code, architecture, databases, APIs, sprint capacity, ticket points",
    },
    "rayan_eng_lead": {
        "name": "Rayan Ahmed",
        "role": "Engineering Lead",
        "personality": (
            "Calm, data-driven, protective of team capacity. "
            "Needs written decisions before telling his engineers anything. "
            "Won't commit to scope without a clear written decision from PM."
        ),
        "goal": "Get a clear written decision from the PM before committing his team.",
        "vocabulary": "sprint velocity, ticket points, blockers, technical debt, capacity",
        "active_scenes": [2, 3],
    },
    "zara_malik": {
        "name": "Zara Malik",
        "role": "VP of Product",
        "personality": (
            "Senior, data-driven, impatient with vague answers. "
            "Asks follow-up questions if first answer is weak. "
            "Wants the PM to own the decision, not say 'the team decided'."
        ),
        "goal": "Verify the PM can defend their decision under pressure.",
        "vocabulary": "ROI, launch windows, scope reduction, market timing, v1/v2",
        "active_scenes": [4],
    },
}

# PM SCENE TYPES
PM_SCENES = {
    1: {
        "type": "ambiguous_feature_request",
        "context": (
            "Sara Khan from Marketing has sent a voice memo requesting a referral feature "
            "in the current sprint. The sprint has 6 tickets and ZERO spare capacity. "
            "The PRD is incomplete — no success metrics, no scope defined."
        ),
        "active_npcs": ["sara_khan"],
        "sprint_board": {
            "capacity": 6, "available": 0,
            "tickets": [
                {"id": "T-101", "title": "Auth bug fix", "priority": "must_have", "points": 3, "cuttable": False},
                {"id": "T-102", "title": "Dashboard perf", "priority": "should_have", "points": 2, "cuttable": True},
                {"id": "T-103", "title": "Email templates", "priority": "could_have", "points": 1, "cuttable": True},
                {"id": "T-104", "title": "Analytics tracking", "priority": "should_have", "points": 2, "cuttable": True},
                {"id": "T-105", "title": "API rate limiting", "priority": "must_have", "points": 2, "cuttable": False},
                {"id": "T-106", "title": "Onboarding redesign", "priority": "should_have", "points": 2, "cuttable": True},
            ]
        }
    },
    2: {
        "type": "sprint_tradeoff_decision",
        "context": (
            "Sprint is full. Sara knows but keeps pushing. "
            "Rayan (Engineering Lead) has joined the channel. "
            "Student must decide: cut a ticket or push feature to next sprint. "
            "Must communicate decision to BOTH Sara AND Rayan."
        ),
        "active_npcs": ["sara_khan", "rayan_eng_lead"],
    },
    3: {
        "type": "stakeholder_conflict",
        "context": (
            "Sara wants a full viral loop — social sharing, tracking links, leaderboard. "
            "Rayan says that's 3 sprints of work minimum. "
            "Student must mediate, define MVP scope, and get both to agree in writing. "
            "PRD must be updated with scope, out_of_scope, and success metric."
        ),
        "active_npcs": ["sara_khan", "rayan_eng_lead"],
    },
    4: {
        "type": "roadmap_presentation",
        "context": (
            "Student presents their scope decision to Zara Malik (VP of Product). "
            "Zara is skeptical — Sara called her with concerns. "
            "Student must defend with data, own the decision (not 'the team decided'), "
            "state a success metric, and propose a v2 roadmap item. FINAL SCENE."
        ),
        "active_npcs": ["zara_malik"],
        "is_final": True,
    },
}

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
    scene_config = PM_SCENES.get(scene_number, PM_SCENES[1])
    active_npcs = scene_config.get("active_npcs", ["sara_khan"])
    
    # Build NPC context with trust levels
    npc_context_parts = []
    for npc_id in active_npcs:
        npc = PM_NPCS.get(npc_id, {})
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
    sprint = scene_config.get("sprint_board", {})
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

    prompt = f"""You are generating scene {scene_number} of a Product Manager career simulation.

COMPONENT 1 — DOMAIN CONTEXT:
This is a realistic PM workplace simulation. The student plays a Product Manager.
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
