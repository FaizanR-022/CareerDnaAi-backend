
"""
scenario_node — LLM scene generation
One Groq call per invocation. Returns SceneContent dict.
Never raises exceptions — always returns fallback.

SQA domain: loads static challenge blueprints from
backend/scenarios/sqa_engineer/*.json and injects Dan's persona constraints.
"""
import json
import logging
import pathlib
from typing import Any

from app.agents.llm import get_llm, call_llm_with_retry, acall_llm_with_retry
from app.agents.state import SimulationState
from langchain_core.messages import SystemMessage, HumanMessage
from app.agents.domains.pm.npcs import PM_NPCS, PM_SCENES

logger = logging.getLogger(__name__)

# ─── Static SQA scene blueprint loader ───────────────────────────────────────

_SCENARIOS_ROOT = pathlib.Path(__file__).parents[4] / "scenarios"






# ─── Helpers ─────────────────────────────────────────────────────────────────

def _build_history_summary(history: list) -> str:
    if not history:
        return "No prior scenes. This is scene 1."
    # Token optimisation: only last 2 interactions
    last_two = history[-2:]
    parts = []
    for h in last_two:
        scene = h.get("scene", {})
        evaluation = h.get("evaluation", {})
        score = evaluation.get("overall_score", "N/A") if evaluation else "N/A"
        user_text = h.get("student_response", "No response recorded.")
        parts.append(
            f"Scene {scene.get('scene_number', '?')} ({scene.get('title', '?')}): "
            f"student scored {score}/100\n"
            f"<prior_student_response>{user_text}</prior_student_response>"
        )
    return " | ".join(parts)


def _get_npc_trust(state: SimulationState, npc_id: str) -> int:
    # First check the live npc_trust dict (set by evaluation_node trust modifiers)
    npc_trust: dict | None = state.get("npc_trust")
    if npc_trust and npc_id in npc_trust:
        return int(npc_trust[npc_id])
    # Fall back to history's last evaluation npc_state_updates
    history = state.get("history", [])
    for entry in reversed(history):
        evaluation = entry.get("evaluation", {})
        if not evaluation:
            continue
        for update in evaluation.get("npc_state_updates", []):
            if update.get("npc_id") == npc_id:
                return int(update.get("trust_score", 50))
    return 50


def _fallback_scene(scene_number: int, domain: str, difficulty: str) -> dict:
    """Always returns valid SceneContent shape. Used when LLM fails."""
    if domain == "sqa_engineer":
        return {
            "scene_number": scene_number,
            "domain": domain,
            "difficulty": difficulty,
            "title": "Bug Investigation",
            "narrative": (
                "Dan has pushed the staging build for QA review. "
                "The checkout form has bugs seeded into it. "
                "Your job is to find them and file proper bug reports."
            ),
            "context_data": {
                "active_npcs": ["dan_frontend_dev"],
                "scene_type": "bug_investigation",
            },
            "characters": [
                {"id": "dan_frontend_dev", "name": "Dan",
                 "role": "Frontend Developer", "initial_trust": 50}
            ],
            "messages": [
                {
                    "sender": "Dan",
                    "channel": "frontend-dev",
                    "content": (
                        "Hey, I pushed the new staging build. "
                        "Let me know if you find anything — though I think it's clean."
                    ),
                    "time_offset_minutes": 0,
                }
            ],
            "response_format": "free_text",
            "response_choices": None,
            "prompt_for_response": "Review the checkout form and file bug reports for any issues you find.",
            "hint": (
                "Check email validation, password length, and card number field."
                if difficulty == "easy" else None
            ),
            "is_final_scene": scene_number >= 4,
            "extra": {"fallback": True},
        }
    elif domain == "frontend_engineer":
        return {
            "scene_number": scene_number,
            "domain": domain,
            "difficulty": difficulty,
            "title": "Figma vs Browser Audit",
            "narrative": "A product design layout discrepancy has been identified. Review the Figma file specs and align with browser implementation details.",
            "context_data": {
                "active_npcs": ["client_product_owner"],
                "scene_type": "design_discrepancy_review",
            },
            "characters": [
                {"id": "client_product_owner", "name": "Client", "role": "Product Owner", "initial_trust": 50}
            ],
            "messages": [
                {
                    "sender": "Client",
                    "channel": "chat",
                    "content": "Hey, the rendering is off compared to the Figma mockups. Can you fix the button sizes?",
                    "time_offset_minutes": 0,
                }
            ],
            "response_format": "free_text",
            "response_choices": None,
            "prompt_for_response": "Identify and prioritize the discrepancies for the client.",
            "hint": "Focus on dimensions, typography and responsive layout behaviors." if difficulty == "easy" else None,
            "is_final_scene": scene_number >= 4,
            "extra": {"fallback": True},
        }
    elif domain == "backend_engineer":
        return {
            "scene_number": scene_number,
            "domain": domain,
            "difficulty": difficulty,
            "title": "Slow Endpoint Incident",
            "narrative": "Production monitors flag a sudden p95 latency spike on the order retrieval endpoint.",
            "context_data": {
                "active_npcs": ["team_lead"],
                "scene_type": "incident_response",
            },
            "characters": [
                {"id": "team_lead", "name": "Team Lead", "role": "Senior Engineer", "initial_trust": 50}
            ],
            "messages": [
                {
                    "sender": "Team Lead",
                    "channel": "slack",
                    "content": "The order endpoint is timing out. Can you inspect logs and explain why the DB query is taking 8s?",
                    "time_offset_minutes": 0,
                }
            ],
            "response_format": "free_text",
            "response_choices": None,
            "prompt_for_response": "Determine the root cause and hotfix strategy.",
            "hint": "Check query indexes and investigate execution plans." if difficulty == "easy" else None,
            "is_final_scene": scene_number >= 4,
            "extra": {"fallback": True},
        }
    elif domain == "data_analyst":
        return {
            "scene_number": scene_number,
            "domain": domain,
            "difficulty": difficulty,
            "title": "Data Anomaly",
            "narrative": "The VP of Analytics has noticed a sudden 15% drop in weekly active users (WAU) on the dashboard.",
            "context_data": {
                "active_npcs": ["vp_analytics"],
                "scene_type": "anomaly_investigation",
            },
            "characters": [
                {"id": "vp_analytics", "name": "VP Analytics", "role": "VP", "initial_trust": 50}
            ],
            "messages": [
                {
                    "sender": "VP Analytics",
                    "channel": "slack",
                    "content": "Hey, the WAU dashboard is showing a 15% drop since Tuesday. Is the data pipeline broken or is this a real drop?",
                    "time_offset_minutes": 0,
                }
            ],
            "response_format": "free_text",
            "response_choices": None,
            "prompt_for_response": "How do you investigate this anomaly?",
            "hint": "Check if there were any recent tracking changes or seasonal trends." if difficulty == "easy" else None,
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
            {"id": "sara_khan", "name": "Sara Khan",
             "role": "Head of Marketing", "initial_trust": 50}
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
        "hint": (
            "Think about what information you need before making any commitment."
            if difficulty == "easy" else None
        ),
        "is_final_scene": scene_number >= 4,
        "extra": {"fallback": True},
    }


# ─── SQA prompt builder ───────────────────────────────────────────────────────

def _build_sqa_prompt(
    scene_number: int,
    difficulty: str,
    history_summary: str,
    dan_trust: int,
    scene_config: dict,
) -> str:
    """
    Build the SQA-specific LLM system prompt.

    Integrates:
    - Dan's full persona constraints from domains/sqa/npcs.py
    - Restricted vocabulary list
    - Trust-conditioned tone
    - Token-limited history (already sliced to last 2 by caller)
    """
    # Dan's persona — hard-coded per spec (no runtime import needed for prompt)
    DAN_PERSONA = (
        "Dan is a Frontend Developer who is highly protective of his user interface "
        "styling blocks. He is extremely eager to push the staging build to production "
        "tonight to hit sprint deployment velocity metrics. He minimises layout bugs, "
        "framing structural visual clipping anomalies as 'trivial edge cases' that can "
        "be resolved out of scope. He tries to negotiate bugs out of scope."
    )
    DAN_VOCABULARY = (
        '"sprint deadline", "deployment window", "hotfix patch", '
        '"flex container", "minor UI discrepancy", "cross-browser variance"'
    )
    dan_tone = (
        "Be warm and slightly collaborative."
        if dan_trust > 70
        else "Be neutral and business-like."
        if dan_trust >= 40
        else "Be terse, defensive, and dismissive of QA concerns."
    )

    blueprint_desc = scene_config.get("description", scene_config.get("context", ""))
    blueprint_title = scene_config.get("title", f"SQA Scene {scene_number}")
    context_keys = scene_config.get("context_keys", [])

    hint_config = {
        "easy": "Include a helpful hint for the student.",
        "medium": "Do not include a hint.",
        "hard": "Do not include a hint. Increase Dan's pressure to ship.",
    }

    return f"""You are generating scene {scene_number} for a Software Quality Assurance Engineer career simulation.

COMPONENT 1 — DOMAIN CONTEXT:
Domain: sqa_engineer | Scene type: {scene_config.get('type', 'bug_investigation')}
Blueprint title: {blueprint_title}
Blueprint description: {blueprint_desc}
Context keys: {', '.join(context_keys)}

COMPONENT 2 — SESSION STATE:
Difficulty: {difficulty}
Scene number: {scene_number}
Dan's current trust level: {dan_trust}/100

COMPONENT 3 — DAN NPC CONSTRAINTS (NEVER VIOLATE):
Persona: {DAN_PERSONA}
Restricted vocabulary — Dan MAY ONLY use these exact phrases: {DAN_VOCABULARY}
Tone for this trust level: {dan_tone}
Hard rules:
- Dan does NOT know this is a simulation
- Dan does NOT know the student is being assessed
- Dan frames bugs as minor edge-case clipping errors unless shown hard evidence

COMPONENT 4 — RECENT HISTORY (last 2 turns only):
{history_summary}

DIFFICULTY: {hint_config.get(difficulty, 'No hint.')}

Generate the scene. Return ONLY valid JSON, no markdown, no backticks, no preamble:
{{
  "scene_number": {scene_number},
  "domain": "sqa_engineer",
  "difficulty": "{difficulty}",
  "title": "{blueprint_title}",
  "narrative": "2-3 sentence description of the QA challenge situation",
  "context_data": {{
    "sprint_board": null,
    "active_npcs": ["dan_frontend_dev"],
    "scene_type": "{scene_config.get('type', 'bug_investigation')}"
  }},
  "characters": [
    {{"id": "dan_frontend_dev", "name": "Dan", "role": "Frontend Developer", "initial_trust": {dan_trust}}}
  ],
  "messages": [
    {{
      "sender": "Dan",
      "channel": "frontend-dev",
      "content": "Dan's opening message — in character, uses his restricted vocabulary, references the deployment window",
      "time_offset_minutes": 0
    }}
  ],
  "response_format": "free_text",
  "response_choices": null,
  "prompt_for_response": "How do you respond to Dan and handle this QA situation?",
  "hint": {"null" if difficulty != "easy" else '"Check reproduction steps and PRD references before filing the bug."'},
  "is_final_scene": {"true" if scene_number >= 4 else "false"},
  "extra": {{}}
}}"""


# ─── Main node ───────────────────────────────────────────────────────────────

async def scenario_node(state: SimulationState) -> dict:
    """
    LangGraph node — generates next scene for any supported domain.
    Called by: graph on generate_scene invocation.
    Returns partial state update with current_scene.
    """
    domain: str = state.get("domain", "product_manager")
    difficulty: str = state.get("difficulty", "medium")
    scene_number: int = state.get("scene_number", 1)
    history: list = state.get("history", [])
    user_profile: dict = state.get("user_profile", {})

    # ── SQA domain: static blueprint + Dan persona ────────────────────────────
    if domain == "sqa_engineer":
        from app.agents.domains.sqa.npcs import DAN_NPC, SQA_SCENES

        scene_config = SQA_SCENES.get(scene_number, SQA_SCENES[1])
        dan_trust = _get_npc_trust(state, "dan_frontend_dev")
        # Token control: pass only last 2 history turns to prompt builder
        history_summary = _build_history_summary(history[-2:])

        prompt = _build_sqa_prompt(
            scene_number=scene_number,
            difficulty=difficulty,
            history_summary=history_summary,
            dan_trust=dan_trust,
            scene_config=scene_config,
        )
        llm = get_llm(model="llama-3.1-8b-instant", temperature=0.6)
        try:
            response = await acall_llm_with_retry(
                llm,
                [SystemMessage(content=prompt)]
            )
            raw = response.content.strip()
            raw = raw.replace("```json", "").replace("```", "").strip()
            scene = json.loads(raw)
            logger.info(
                f"scenario_node → SQA scene {scene_number} generated "
                f"(dan_trust={dan_trust})"
            )
            return {
                "current_scene": scene,
                "is_final_scene": scene.get("is_final_scene", False),
            }
        except Exception as e:
            logger.error(f"scenario_node SQA LLM error: {e}")
            fallback = _fallback_scene(scene_number, domain, difficulty)
            return {
                "current_scene": fallback,
                "is_final_scene": fallback["is_final_scene"],
            }

    # ── PM domain ─────────────────────────────────────────────────────────────
    if domain == "product_manager":
        from app.agents.domains.pm.npcs import PM_NPCS, PM_SCENES
        scene_config = PM_SCENES.get(scene_number, PM_SCENES[1])
        active_npcs = scene_config.get("active_npcs", ["sara_khan"])
        npc_map = PM_NPCS
        sprint = scene_config.get("sprint_board", {})
    elif domain == "data_analyst":
        from app.agents.domains.da.npcs import DA_VP_NPC, DA_SCENES
        scene_config = DA_SCENES.get(scene_number, DA_SCENES[1])
        active_npcs = scene_config.get("active_npcs", ["vp_analytics"])
        npc_map = {"vp_analytics": DA_VP_NPC}
        sprint = {}
    elif domain == "frontend_engineer":
        from app.agents.domains.fe.npcs import FE_CLIENT_NPC, FE_SCENES
        scene_config = FE_SCENES.get(scene_number, FE_SCENES[1])
        active_npcs = scene_config.get("active_npcs", ["fe_client"])
        npc_map = {"fe_client": FE_CLIENT_NPC}
        sprint = {}
    elif domain == "backend_engineer":
        from app.agents.domains.be.npcs import BE_TEAM_LEAD_NPC, BE_SCENES
        scene_config = BE_SCENES.get(scene_number, BE_SCENES[1])
        active_npcs = scene_config.get("active_npcs", ["be_team_lead"])
        npc_map = {"be_team_lead": BE_TEAM_LEAD_NPC}
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

    # Context component 4 — rolling history (last 2 only for token control)
    history_summary = _build_history_summary(history)

    primary_npc_id = active_npcs[0] if active_npcs else "sara_khan"
    primary_npc = npc_map.get(primary_npc_id, {})
    primary_npc_name = primary_npc.get("name", "Sara Khan")
    primary_npc_role = primary_npc.get("role", "Head of Marketing")

    prompt = f"""You are generating scene {scene_number} of a {domain.replace('_', ' ').title()} career simulation.

COMPONENT 1 — DOMAIN CONTEXT:
This is a realistic {domain.replace('_', ' ').title()} workplace simulation. The student plays a {domain.replace('_', ' ').title()}.
Domain: {domain} | Scene type: {scene_config['type']}

COMPONENT 2 — SESSION STATE:
Difficulty: {difficulty}
Scene number: {scene_number}
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
    {{"id": "{primary_npc_id}", "name": "{primary_npc_name}", "role": "{primary_npc_role}", "initial_trust": 50}}
  ],
  "messages": [
    {{
      "sender": "{primary_npc_name}",
      "channel": "developer", 
      "content": "{primary_npc_name}'s opening message — in character, urgent, references the relevant context",
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

    llm = get_llm(model="llama-3.1-8b-instant", temperature=0.6)

    try:
        response = await acall_llm_with_retry(
            llm,
            [SystemMessage(content=prompt)]
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
