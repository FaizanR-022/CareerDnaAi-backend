
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
        fallback = {
            "scene_number": scene_number,
            "domain": domain,
            "difficulty": difficulty,
            "characters": [
                {"id": "fe_client", "name": "SuperMart Client", "role": "Product Owner", "initial_trust": 50}
            ],
            "messages": [
                {
                    "sender": "SuperMart Client",
                    "channel": "slack",
                    "content": "Hey, we need to sort out the SuperMart responsive layout. Let's get this done.",
                    "time_offset_minutes": 0,
                }
            ],
            "response_format": "interactive_workspace",
            "prompt_for_response": "Complete the frontend layout and design tasks.",
            "is_final_scene": False,
            "extra": {
                "fallback": True,
                "figma_mockup_url": "https://www.figma.com/design/therapeutic-healthcare-theme",
                "broken_browser_implementation_url": "https://supermart-therapeutic-layout.vercel.app"
            },
            "context_data": {
                "active_npcs": ["fe_client"]
            },
            "interactive_config": {}
        }
        if scene_number == 1:
            fallback["title"] = "Design System & Theme Calibration (Fallback)"
            fallback["narrative"] = "SuperMart requires a high-contrast therapeutic theme. Resolve accessibility contrast issues before building the layout."
            fallback["interactive_config"]["design_review"] = {
                "is_completed": False,
                "problem_statement": "Select the most accessible contrast ratio for the SuperMart checkout button.",
                "requires_reason": True,
                "options": [
                    {"id": "mockup_a", "title": "High Contrast Theme", "is_accessible": True, "metrics": {"contrast_ratio": "4.5:1"}},
                    {"id": "mockup_b", "title": "Low Contrast Theme", "is_accessible": False, "metrics": {"contrast_ratio": "1.8:1"}}
                ]
            }
        elif scene_number == 2:
            fallback["title"] = "Theme Verification & Structural Layout (Fallback)"
            fallback["narrative"] = "With the theme approved, map out the 5-slot homepage wireframe ensuring critical e-commerce blocks are highly visible."
            fallback["interactive_config"]["design_review"] = {
                "is_completed": True, 
                "problem_statement": "Review previous theme choices.",
                "requires_reason": True,
                "options": [{"id": "mockup_a", "title": "High Contrast Theme", "is_accessible": True, "metrics": {"contrast_ratio": "4.5:1"}}]
            }
            fallback["interactive_config"]["wireframe_builder"] = {
                "is_completed": False,
                "problem_statement": "Drag and drop the 5 most critical e-commerce blocks in the correct visual hierarchy.",
                "available_blocks": [{"id": "blk_hero", "label": "Hero Banner"}],
                "canvas_slots": 5,
                "expected_stack_sequence": ["blk_header", "blk_hero", "blk_features", "blk_top_seller", "blk_footer"]
            }
        elif scene_number == 3:
            fallback["title"] = "Wireframe Grid & Mobile CSS Polish (Fallback)"
            fallback["narrative"] = "The wireframe is approved. Now, fix the CSS grid for the mobile viewport. The product cards are overflowing off the 375px screen."
            fallback["interactive_config"]["wireframe_builder"] = {
                "is_completed": True, 
                "problem_statement": "Review established wireframe.",
                "available_blocks": [{"id": "blk_hero", "label": "Hero Banner"}],
                "canvas_slots": 5,
                "expected_stack_sequence": ["blk_header", "blk_hero", "blk_features", "blk_top_seller", "blk_footer"]
            }
            fallback["interactive_config"]["css_sandbox"] = {
                "is_completed": False,
                "target_viewport": "mobile",
                "viewport_width": 375,
                "problem_statement": "Ensure a responsive, wrapping single-column layout for mobile.",
                "raw_css": ".supermart-container {\n  display: flex;\n  width: 100%;\n  {{VAR_1}}\n}",
                "editable_variables": {
                    "VAR_1": {
                        "current": "flex-wrap: nowrap;",
                        "options": ["flex-wrap: nowrap;", "flex-wrap: wrap;", "flex-direction: column;"],
                        "correct": "flex-direction: column;"
                    }
                }
            }
        elif scene_number >= 4:
            fallback["title"] = "Accessibility Validation & Final Mobile Build (Fallback)"
            fallback["narrative"] = "Final pass. Ensure the mobile layout CSS works with the high-contrast accessibility theme established in Scene 1."
            fallback["interactive_config"]["design_review"] = {
                "is_completed": True, 
                "problem_statement": "Final contrast check.",
                "requires_reason": True,
                "options": [{"id": "mockup_a", "title": "High Contrast Theme", "is_accessible": True, "metrics": {"contrast_ratio": "4.5:1"}}]
            }
            fallback["interactive_config"]["css_sandbox"] = {
                "is_completed": False,
                "target_viewport": "mobile",
                "viewport_width": 375,
                "problem_statement": "Finalize mobile styling.",
                "raw_css": ".supermart-container {\n  display: flex;\n  width: 100%;\n  flex-direction: column;\n}",
                "editable_variables": {}
            }
            fallback["is_final_scene"] = True
            
        return fallback
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
        fallback = {
            "scene_number": scene_number,
            "domain": domain,
            "difficulty": difficulty,
            "title": f"Data Analyst Scene {scene_number}",
            "narrative": "Acme Corp has noticed anomalies in the transaction log and suspects institutional dumping.",
            "characters": [
                {"id": "sara_developer", "name": "Sara", "role": "Data Developer", "initial_trust": 50},
                {"id": "acme_corp_client", "name": "Acme Corp", "role": "Client", "initial_trust": 50}
            ],
            "messages": [
                {
                    "sender": "Sara",
                    "channel": "slack",
                    "content": "Hey, Acme Corp flagged some weird transaction volumes. We need to check the pipeline and look for institutional dumping.",
                    "time_offset_minutes": 0,
                }
            ],
            "response_format": "interactive",
            "prompt_for_response": "Configure the pipeline to begin investigation.",
            "hint": "Impute the mean and keep the first duplicate." if difficulty == "easy" else None,
            "is_final_scene": False,
            "interactive_config": {},
            "extra": {"fallback": True},
            "context_data": {
                "active_npcs": [
                    {"id": "sara_developer", "name": "Sara", "role": "Data Developer", "initial_trust": 50, "goal": "Ensure the data pipeline and queries are functioning correctly.", "vocabulary": "pipeline, imputation, SQL"},
                    {"id": "acme_corp_client", "name": "Acme Corp", "role": "Client", "initial_trust": 50, "goal": "Understand if there is institutional dumping or RSI divergence.", "vocabulary": "institutional dumping, RSI divergence"}
                ],
                "interactive_tasks": {}
            }
        }

        if scene_number == 1:
            fallback["interactive_config"] = {
                "editor_type": "pipeline_config",
                "available_imputation_strategies": ["impute_mean", "drop_rows", "impute_zero"],
                "available_duplicate_handling": ["keep_first", "keep_last", "drop_all"]
            }
            fallback["context_data"]["interactive_tasks"]["data_explorer"] = {
                "problem_statement": "The transaction log contains missing values and duplicates. Use the data pipeline to handle them.",
                "flagged_constraints": ["null values in the RSI column", "duplicates in the ticker column"],
                "schema": {"Timestamp": "VARCHAR", "Ticker": "VARCHAR", "Volume": "INTEGER", "RSI": "INTEGER", "Type": "VARCHAR"},
                "pipeline_config": {
                    "null_handling": {"options": ["drop rows with null values", "impute null values with mean/median/mode"], "correct": "drop rows with null values"},
                    "duplicate_handling": {"options": ["drop duplicates", "keep duplicates"], "correct": "drop duplicates"}
                },
                "table_data": [
                    {"index": "1", "Timestamp": "2022-01-01", "Ticker": "AAPL", "Volume": "100", "RSI": "null", "Type": "buy", "issues": "Error: Null RSI"},
                    {"index": "2", "Timestamp": "2022-01-02", "Ticker": "AAPL", "Volume": "200", "RSI": "50", "Type": "sell", "issues": "OK"},
                    {"index": "3", "Timestamp": "2022-01-03", "Ticker": "AAPL", "Volume": "300", "RSI": "null", "Type": "buy", "issues": "Error: Null RSI"},
                    {"index": "4", "Timestamp": "2022-01-04", "Ticker": "AAPL", "Volume": "400", "RSI": "55", "Type": "sell", "issues": "OK"},
                    {"index": "5", "Timestamp": "2022-01-05", "Ticker": "AAPL", "Volume": "500", "RSI": "60", "Type": "buy", "issues": "OK"},
                    {"index": "6", "Timestamp": "2022-01-06", "Ticker": "AAPL", "Volume": "600", "RSI": "null", "Type": "sell", "issues": "Error: Null RSI"},
                    {"index": "7", "Timestamp": "2022-01-07", "Ticker": "AAPL", "Volume": "700", "RSI": "65", "Type": "buy", "issues": "OK"},
                    {"index": "8", "Timestamp": "2022-01-08", "Ticker": "AAPL", "Volume": "800", "RSI": "null", "Type": "sell", "issues": "Error: Null RSI"},
                    {"index": "9", "Timestamp": "2022-01-09", "Ticker": "AAPL", "Volume": "900", "RSI": "70", "Type": "buy", "issues": "OK"},
                    {"index": "10", "Timestamp": "2022-01-10", "Ticker": "AAPL", "Volume": "1000", "RSI": "75", "Type": "sell", "issues": "OK"},
                    {"index": "11", "Timestamp": "2022-01-11", "Ticker": "AAPL", "Volume": "1100", "RSI": "null", "Type": "buy", "issues": "Error: Null RSI"},
                    {"index": "12", "Timestamp": "2022-01-12", "Ticker": "AAPL", "Volume": "1200", "RSI": "80", "Type": "sell", "issues": "OK"},
                    {"index": "13", "Timestamp": "2022-01-13", "Ticker": "AAPL", "Volume": "1300", "RSI": "null", "Type": "buy", "issues": "Error: Null RSI"},
                    {"index": "14", "Timestamp": "2022-01-14", "Ticker": "AAPL", "Volume": "1400", "RSI": "85", "Type": "sell", "issues": "OK"},
                    {"index": "15", "Timestamp": "2022-01-15", "Ticker": "AAPL", "Volume": "1500", "RSI": "null", "Type": "buy", "issues": "Error: Null RSI"}
                ]
            }
        elif scene_number == 2:
            fallback["prompt_for_response"] = "Build a SQL query to extract the required data."
            fallback["interactive_config"] = {
                "editor_type": "sql",
                "initial_query": None
            }
            fallback["context_data"]["interactive_tasks"]["query_builder"] = {
                "problem_statement": "Write a query to extract timestamp and volume.",
                "editor_type": "sql",
                "default_code": "-- Type SELECT timestamp, volume FROM data...",
                "helper_snippets": ["SELECT timestamp, volume", "FROM transaction_log"]
            }
        elif scene_number == 3:
            fallback["prompt_for_response"] = "Write Python code to analyze the data."
            fallback["interactive_config"] = {
                "editor_type": "python",
                "initial_code": None
            }
            fallback["context_data"]["interactive_tasks"]["python_sandbox"] = {
                "is_completed": False,
                "problem_statement": "Use python to visualize the data.",
                "editor_type": "python",
                "default_code": "# Type df.plot(x='timestamp', y='volume')...",
                "helper_snippets": ["df.plot(x='timestamp', y='volume')", "print(df.describe())"],
                "validation": {"required_functions": ["plot", "describe"]}
            }
            fallback["context_data"]["sidebar_guides"] = {
                "anomaly_guide": {
                    "title": "Anomaly Guide",
                    "institutional_divergence": "Explanation of institutional divergence.",
                    "rsi_momentum": "Explanation of RSI momentum."
                }
            }
        elif scene_number >= 4:
            fallback["prompt_for_response"] = "Select the correct hypothesis based on your findings."
            fallback["interactive_config"] = {
                "editor_type": "insights",
                "hypothesis_options": ["hyp_divergence", "hyp_seasonality", "hyp_bot_traffic"]
            }
            fallback["context_data"]["interactive_tasks"]["insights_console"] = {
                "problem_statement": "Identify the primary cause of the anomaly.",
                "editor_type": "insights",
                "hypothesis_options": [
                    {"id": "hyp_1", "title": "Institutional Dumping", "description": "Large volume sell-offs.", "is_correct": True},
                    {"id": "hyp_2", "title": "Retail Panic", "description": "Small volume sell-offs.", "is_correct": False},
                    {"id": "hyp_3", "title": "Bot Malfunction", "description": "High frequency tiny trades.", "is_correct": False}
                ]
            }
            fallback["is_final_scene"] = True
            
        return fallback
    pm_context_data = {
        "active_npcs": ["sara_khan"],
    }
    if scene_number in (1, 3, 4):
        pm_context_data["sprint_board"] = PM_SCENES[1]["sprint_board"]
    if scene_number in (2, 3, 4):
        pm_context_data["prd_data"] = PM_SCENES[1]["prd_data"]

    return {
        "scene_number": scene_number,
        "domain": domain,
        "difficulty": difficulty,
        "title": "Feature Request",
        "narrative": (
            "Sara Khan from Marketing has sent you a voice memo. "
            "She's requesting a referral feature in the current sprint."
        ),
        "context_data": pm_context_data,
        "characters": [
            {"id": "sara_khan", "name": "Sara Khan",
             "role": "Head of Marketing", "initial_trust": 50}
        ],
        "messages": [
            {
                "sender": "Sara Khan",
                "channel": "sara_khan",
                "content": "Hey! We really need the referral feature in this sprint. Can we make it happen?",
                "time_offset_minutes": 0,
            }
        ],
        "response_format": "free_text",
        "response_choices": None,
        "prompt_for_response": "Review the referral feature request against the current sprint capacity, negotiate with Sara, and explain that the current PRD lacks success metrics and scope.",
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

BUG & SCENARIO GENERATION (invent fresh specifics — do not reuse the exact bugs/variants from prior sessions):
- For bugs, invent realistic technical details, exact input field names, or error codes that vary each time.
- Vary the exact environment specifics (e.g. Chrome vs Firefox, Android vs iOS) and layout issues each generation.
- Never output identical bug descriptions twice.

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
            logger.info(f"[llm-prompt] {prompt}")
            response = await acall_llm_with_retry(
                llm,
                [SystemMessage(content=prompt)]
            )
            raw = response.content.strip()
            raw = raw.replace("```json", "").replace("```", "").strip()
            scene = json.loads(raw)
            if scene_number >= 4:
                scene["is_final_scene"] = True
                
            logger.info(
                f"[LLM_OK] scenario_node → SQA scene {scene_number} generated from LLM "
                f"(dan_trust={dan_trust})"
            )
            logger.info(f"[LLM_RESPONSE] scenario_node SQA scene {scene_number}: {raw}")
            return {
                "current_scene": scene,
                "is_final_scene": scene.get("is_final_scene", False),
            }
        except Exception as e:
            logger.warning(
                f"[LLM_FALLBACK] scenario_node SQA scene {scene_number} → using static fallback "
                f"scene (reason: {e})"
            )
            fallback = _fallback_scene(scene_number, domain, difficulty)
            return {
                "current_scene": fallback,
                "is_final_scene": fallback["is_final_scene"],
            }

    # ── DA domain: interactive with structured output ──────────────────────────
    if domain == "data_analyst":
        from app.agents.domains.da.npcs import DA_NPCS, DA_SCENES
        from app.schemas.agent_contracts import SceneContent, DAScene1Content
        
        scene_config = DA_SCENES.get(scene_number, DA_SCENES[1])
        active_npcs = scene_config.get("active_npcs", [])
        
        # Build NPC context with trust levels
        npc_context_parts = []
        for npc_id in active_npcs:
            npc = DA_NPCS.get(npc_id, {})
            trust = _get_npc_trust(state, npc_id)
            npc_context_parts.append(
                f"- {npc.get('name')} ({npc.get('role')}): "
                f"trust {trust}/100, goal: {npc.get('goal')}, "
                f"vocabulary: {npc.get('vocabulary')}"
            )
        npc_context = "\n".join(npc_context_parts)
        
        prompt = f"""You are generating scene {scene_number} of a Data Analyst career simulation.
        
COMPONENT 1 — DOMAIN CONTEXT:
Domain: data_analyst | Scene type: {scene_config.get('type')}
{scene_config.get('context')}

COMPONENT 2 — SESSION STATE:
Difficulty: {difficulty}
Scene number: {scene_number}
Active NPCs and trust levels:
{npc_context}

COMPONENT 3 — TECHNICAL CONSTRAINTS:
For this scene, configure the interactive_config based on the scene type exactly:
- Scene 1 (pipeline_config): interactive_config.editor_type = "pipeline_config"
- Scene 2 (sql_editor): interactive_config.editor_type = "sql"
- Scene 3 (python_editor): interactive_config.editor_type = "python"
- Scene 4 (insights_console): interactive_config.editor_type = "insights"

Ensure response_format is "interactive". Make dialogue natural.
"""

        if scene_number == 1:
            prompt += """
COMPONENT 4 — STRICT JSON HIERARCHY:
You must respect the strict boundary between root-level fields and nested context fields.

ROOT-LEVEL FIELDS (You MUST generate these at the top level):
- 'scene_number' (integer)
- 'domain' (string)
- 'difficulty' (string)
- 'title' (string)
- 'narrative' (string)
- 'characters' (array of objects)
- 'messages' (array of objects)
- 'prompt_for_response' (string)
- 'response_format' (string)
- 'interactive_config' (object)
- 'context_data' (object)

NESTED FIELDS:
Do NOT place 'narrative', 'prompt_for_response', or 'interactive_config' inside 'context_data'. They belong at the root.
'context_data' should ONLY contain 'active_npcs' and 'interactive_tasks'.

COMPONENT 5 — SCENE 1 DATA EXPLORER GENERATION:
You must fully populate the context_data.interactive_tasks.data_explorer object.
CRITICAL: You MUST include ALL of the following keys:
1. 'problem_statement' (string)
2. 'flagged_constraints' (array of strings)
3. 'pipeline_config' (object with null_handling and duplicate_handling)
4. 'schema' (mapping of columns to types)
5. 'table_data' (array of 3-20 row objects. EVERY row MUST have an 'issues' key!).
Do not omit any of these keys.
"""
            schema_str = DAScene1Content.model_json_schema()
            prompt += f"\n\nCRITICAL: You MUST return a single valid JSON object. Do NOT wrap it in any tags. It MUST exactly match this JSON schema:\n```json\n{json.dumps(schema_str, indent=2)}\n```\n"
            llm = get_llm(model="llama-3.1-8b-instant", temperature=0.6)
            structured_llm = llm.with_structured_output(DAScene1Content, method="json_mode")
        elif scene_number == 3:
            prompt += """
COMPONENT 4 — SCENE 3 PYTHON SANDBOX GENERATION:
You must fully populate the context_data object for a Python coding task.
CRITICAL: You MUST include ALL of the following keys inside context_data:
1. 'interactive_tasks.python_sandbox': Must include 'editor_type' set to "python", a 'default_code' comment, 3 'helper_snippets' (e.g., "df.plot(...)"), and 'validation' keywords.
2. 'sidebar_guides': Must include the 'anomaly_guide' explaining institutional divergence and RSI momentum to the user.
Do NOT place root-level fields (narrative, messages) inside context_data.
"""
            from app.schemas.agent_contracts import DAScene3Content
            schema_str = DAScene3Content.model_json_schema()
            prompt += f"\n\nCRITICAL: You MUST return a single valid JSON object. Do NOT wrap it in any tags. It MUST exactly match this JSON schema:\n```json\n{json.dumps(schema_str, indent=2)}\n```\n"
            llm = get_llm(model="llama-3.1-8b-instant", temperature=0.6)
            structured_llm = llm.with_structured_output(DAScene3Content, method="json_mode")
        else:
            llm = get_llm(model="llama-3.1-8b-instant", temperature=0.6)
            structured_llm = llm.with_structured_output(SceneContent)

        try:
            logger.info(f"[llm-prompt] {prompt}")
            response = await acall_llm_with_retry(
                structured_llm,
                [SystemMessage(content=prompt)]
            )
            scene_dict = response.model_dump(by_alias=True)
            if scene_number >= 4:
                scene_dict["is_final_scene"] = True
                
            logger.info(f"[LLM_OK] scenario_node → DA scene {scene_number} generated structured")
            return {
                "current_scene": scene_dict,
                "is_final_scene": scene_dict.get("is_final_scene", False),
            }
        except Exception as e:
            logger.warning(
                f"[LLM_FALLBACK] scenario_node DA scene {scene_number} → using static fallback "
                f"(reason: {e})"
            )
            fallback = _fallback_scene(scene_number, domain, difficulty)
            return {
                "current_scene": fallback,
                "is_final_scene": fallback["is_final_scene"],
            }

    # ── FE domain: interactive with structured output ──────────────────────────
    if domain == "frontend_engineer":
        from app.agents.domains.fe.npcs import FE_CLIENT_NPC, FE_SCENES
        from app.schemas.agent_contracts import (
            FEScene1Content, FEScene2Content, FEScene3Content, FEScene4Content, SceneContent, LLMSceneOutput
        )
        
        # Hardcoded static configuration matrix
        SUPERMART_CONFIGS = {
            1: {
                "interactive_config": {
                    "active_tabs": ["design_review"],
                    "design_review": {
                        "is_completed": False,
                        "problem_statement": "Define a clean therapeutic healthcare interface theme. WCAG AA requirements mandate a minimum contrast ratio of 4.5:1 for body copy. Select a modern typography pair and valid primary/background colors below.",
                        "requires_reason": True,
                        "options": [
                            {"id": "mockup_a", "title": "High Contrast Theme", "is_accessible": True, "metrics": {"contrast_ratio": "4.5:1"}},
                            {"id": "mockup_b", "title": "Low Contrast Theme", "is_accessible": False, "metrics": {"contrast_ratio": "1.8:1"}}
                        ]
                    }
                },
                "prompt_for_response": "Complete the frontend layout and design tasks."
            },
            2: {
                "interactive_config": {
                    "active_tabs": ["design_review", "wireframe_builder"],
                    "design_review": {
                        "is_completed": True, 
                        "problem_statement": "Review previous theme choices.",
                        "requires_reason": True,
                        "options": [{"id": "mockup_a", "title": "High Contrast Theme", "is_accessible": True, "metrics": {"contrast_ratio": "4.5:1"}}]
                    },
                    "wireframe_builder": {
                        "is_completed": False,
                        "problem_statement": "Drag and drop the 5 most critical e-commerce blocks in the correct visual hierarchy.",
                        "available_blocks": [{"id": "blk_hero", "label": "Hero Banner"}],
                        "canvas_slots": 5,
                        "expected_stack_sequence": ["blk_header", "blk_hero", "blk_features", "blk_top_seller", "blk_footer"]
                    }
                },
                "prompt_for_response": "Complete the frontend layout and design tasks."
            },
            3: {
                "interactive_config": {
                    "active_tabs": ["wireframe_builder", "css_sandbox"],
                    "wireframe_builder": {
                        "is_completed": True, 
                        "problem_statement": "Review established wireframe.",
                        "available_blocks": [{"id": "blk_hero", "label": "Hero Banner"}],
                        "canvas_slots": 5,
                        "expected_stack_sequence": ["blk_header", "blk_hero", "blk_features", "blk_top_seller", "blk_footer"]
                    },
                    "css_sandbox": {
                        "is_completed": False,
                        "target_viewport": "mobile",
                        "viewport_width": 375,
                        "problem_statement": "Ensure a responsive, wrapping single-column layout for mobile.",
                        "raw_css": ".supermart-container {\n  display: flex;\n  width: 100%;\n  {{VAR_1}}\n}",
                        "editable_variables": {
                            "VAR_1": {
                                "current": "flex-wrap: nowrap;",
                                "options": ["flex-wrap: nowrap;", "flex-wrap: wrap;", "flex-direction: column;"],
                                "correct": "flex-direction: column;"
                            }
                        }
                    }
                },
                "prompt_for_response": "Complete the frontend layout and design tasks."
            },
            4: {
                "interactive_config": {
                    "active_tabs": ["design_review", "css_sandbox"],
                    "design_review": {
                        "is_completed": True, 
                        "problem_statement": "Final contrast check.",
                        "requires_reason": True,
                        "options": [{"id": "mockup_a", "title": "High Contrast Theme", "is_accessible": True, "metrics": {"contrast_ratio": "4.5:1"}}]
                    },
                    "css_sandbox": {
                        "is_completed": False,
                        "target_viewport": "mobile",
                        "viewport_width": 375,
                        "problem_statement": "Finalize mobile styling.",
                        "raw_css": ".supermart-container {\n  display: flex;\n  width: 100%;\n  flex-direction: column;\n}",
                        "editable_variables": {}
                    }
                },
                "prompt_for_response": "Complete the frontend layout and design tasks."
            }
        }
        
        scene_config = FE_SCENES.get(scene_number, FE_SCENES[1])
        active_npcs = scene_config.get("active_npcs", ["fe_client"])
        
        # Build NPC context with trust levels
        npc_context_parts = []
        for npc_id in active_npcs:
            npc = FE_CLIENT_NPC if npc_id == "fe_client" else {}
            trust = _get_npc_trust(state, npc_id)
            npc_context_parts.append(
                f"- {npc.get('name', 'Client')} ({npc.get('role', 'Client')}): "
                f"trust {trust}/100, goal: {npc.get('goal', 'Launch')}, "
                f"vocabulary: {npc.get('vocabulary', 'layout')}"
            )
        npc_context = "\n".join(npc_context_parts)

        prompt = f"""You are generating scene {scene_number} of a Frontend Engineer career simulation.
        
COMPONENT 1 — DOMAIN CONTEXT:
Domain: frontend_engineer | Scene type: {scene_config.get('type', 'frontend')}
{scene_config.get('context', 'SuperMart e-commerce layout build.')}

COMPONENT 2 — SESSION STATE:
Difficulty: {difficulty}
Scene number: {scene_number}
Active NPCs and trust levels:
{npc_context}

COMPONENT 3 — TECHNICAL CONSTRAINTS:
You must ONLY generate the 'title', 'narrative', and NPC 'messages'. 
DO NOT generate any JSON for interactive tasks, interactive_configs, or workspaces.
"""
        
        schema_str = LLMSceneOutput.model_json_schema()
        prompt += f"\n\nCRITICAL: You MUST return a single valid JSON object exactly matching this schema:\n```json\n{json.dumps(schema_str, indent=2)}\n```\n"

        llm = get_llm(model="llama-3.1-8b-instant", temperature=0.6)
        structured_llm = llm.with_structured_output(LLMSceneOutput, method="json_mode")
        
        try:
            logger.info(f"[llm-prompt] {prompt}")
            response = await acall_llm_with_retry(
                structured_llm,
                [SystemMessage(content=prompt)]
            )
            llm_dict = response.model_dump(by_alias=True)
            
            # Assemble Hybrid Payload
            base_config = SUPERMART_CONFIGS.get(scene_number if scene_number <= 4 else 4, SUPERMART_CONFIGS[4])
            schema_cls = {1: FEScene1Content, 2: FEScene2Content, 3: FEScene3Content}.get(scene_number, FEScene4Content)
            
            merged_dict = {
                "scene_number": scene_number,
                "domain": domain,
                "difficulty": difficulty,
                "response_format": "interactive_workspace",
                "is_final_scene": scene_number >= 4,
                "title": llm_dict["title"],
                "narrative": llm_dict["narrative"],
                "messages": llm_dict["messages"],
                "prompt_for_response": base_config["prompt_for_response"],
                "context_data": {
                    "active_npcs": active_npcs
                },
                "interactive_config": base_config["interactive_config"],
                "characters": llm_dict["characters"],
                "extra": {
                    "figma_mockup_url": "https://www.figma.com/design/therapeutic-healthcare-theme",
                    "broken_browser_implementation_url": "https://supermart-therapeutic-layout.vercel.app"
                }
            }
            
            # Validate through Pydantic
            final_scene = schema_cls(**merged_dict).model_dump(by_alias=True)
            
            logger.info(f"[LLM_OK] scenario_node → FE scene {scene_number} generated structured")
            return {
                "current_scene": final_scene,
                "is_final_scene": final_scene.get("is_final_scene", False),
            }
        except Exception as e:
            logger.warning(
                f"[LLM_FALLBACK] scenario_node FE scene {scene_number} → using static fallback "
                f"(reason: {e})"
            )
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
        sprint = (scene_config.get("sprint_board", {}) or PM_SCENES[1].get("sprint_board", {})) if scene_number in (1, 3, 4) else None
        prd_data = (scene_config.get("prd_data", {}) or PM_SCENES[1].get("prd_data", {})) if scene_number in (2, 3, 4) else None
    elif domain == "backend_engineer":
        from app.agents.domains.be.npcs import BE_TEAM_LEAD_NPC, BE_SCENES
        scene_config = BE_SCENES.get(scene_number, BE_SCENES[1])
        active_npcs = scene_config.get("active_npcs", ["be_team_lead"])
        npc_map = {"be_team_lead": BE_TEAM_LEAD_NPC}
        sprint = {}
        prd_data = {}
    else:
        # BE — fallback to PM for now
        from app.agents.domains.pm.npcs import PM_NPCS, PM_SCENES
        scene_config = PM_SCENES.get(1)
        active_npcs = ["sara_khan"]
        npc_map = PM_NPCS
        sprint = scene_config.get("sprint_board", {})
        prd_data = scene_config.get("prd_data", {})

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

    domain_instruction = ""
    if domain == "product_manager" and sprint:
        domain_instruction = f"""
SPRINT BOARD GENERATION (invent fresh tickets — do not reuse ticket names/ids from prior sessions):
- capacity must be exactly {sprint.get('capacity', 6)}
- available must be exactly {sprint.get('available', 0)}
- Invent exactly {sprint.get('capacity', 6)} realistic engineering tickets for "tickets". Each needs:
  id (e.g. "T-201", "T-347" — pick new numbers each time), title (realistic, varied),
  priority ("must_have" | "should_have" | "could_have"), points (1-3), cuttable (true/false).
- Vary ticket subject matter each generation (auth, perf, onboarding, billing, notifications, etc.) —
  never reuse the same six ticket titles verbatim.

PRD DOCUMENT — output the prd_data object exactly as provided below inside context_data.
Do NOT modify the prd_data fields — preserve them verbatim from the seed data.
The student will fill in the empty fields themselves via the frontend PRD editor.

PROBLEM STATEMENT GENERATION (in the "prompt_for_response" field):
- Generate a clear problem statement/instructions detailing exactly what the student needs to achieve in this scene:
  - For Scene 1: Instruct the student to review the sprint board and negotiate the feature request with Sara Khan.
  - For Scene 2: Instruct the student to make a trade-off decision (either cut a ticket to fit the referral or defer it to next sprint) and communicate the choice to both Sara and Rayan.
  - For Scene 3: Instruct the student to align the engineering and marketing stakeholders on an MVP scope and update the PRD's Out of Scope and Success Metrics.
  - For Scene 4: Instruct the student to defend their roadmap decisions to VP Zara Malik using data and ownership of the trade-offs.
"""

    elif domain == "backend_engineer":
        domain_instruction = """
SCENARIO GENERATION (invent fresh specifics — do not reuse details from prior sessions):
- Invent realistic backend incidents, e.g., slow database queries on specific tables, API latency spikes, or memory leaks.
- Vary the exact endpoint paths, error codes, and trace span latency numbers each generation.
"""

    if domain == "product_manager" and sprint:
        sprint_board_template_value = (
            '{"capacity": ' + str(sprint.get('capacity', 6)) +
            ', "available": ' + str(sprint.get('available', 0)) +
            ', "tickets": [ <exactly ' + str(sprint.get('capacity', 6)) +
            ' freshly invented ticket objects per the SPRINT BOARD GENERATION rules above> ] }'
        )
    else:
        sprint_board_template_value = json.dumps(sprint) if sprint else "null"

    # PRD data — pass seed verbatim for PM; null for all other domains
    prd_data_template_value = json.dumps(prd_data) if prd_data else "null"

    # Context component 4 — rolling history (last 2 only for token control)
    history_summary = _build_history_summary(history)

    primary_npc_id = active_npcs[0] if active_npcs else "sara_khan"
    primary_npc = npc_map.get(primary_npc_id, {})
    primary_npc_name = primary_npc.get("name", "Sara Khan")
    primary_npc_role = primary_npc.get("role", "Head of Marketing")
    
    characters_json_list = ",\n    ".join([
        f'{{"id": "{npc_id}", "name": "{npc_map.get(npc_id, {}).get("name", "")}", "role": "{npc_map.get(npc_id, {}).get("role", "")}", "initial_trust": 50}}'
        for npc_id in active_npcs
    ])

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
{scene_config.get('context', '')}
{hard_constraints}
{domain_instruction}

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
    "sprint_board": {sprint_board_template_value},
    "prd_data": {prd_data_template_value},
    "active_npcs": {json.dumps(active_npcs)},
    "scene_type": "{scene_config['type']}"
  }},
  "characters": [
    {characters_json_list}
  ],
  "messages": [
    {{
      "sender": "{primary_npc_name}",
      "channel": "{primary_npc_id}", 
      "content": "{primary_npc_name}'s opening message — in character, urgent, references the relevant context",
      "time_offset_minutes": 0,
      "isAudio": true
    }}
  ],
  "response_format": "free_text",
  "response_choices": null,
  "prompt_for_response": "Concrete problem statement explaining exactly what task the student needs to perform to resolve this scene's challenges",
  "hint": {"null" if difficulty != "easy" else '"Think about what information you need before committing."'},
  "is_final_scene": {"true" if scene_number >= 4 else "false"},
  "voice_memo": {{
    "transcript": "{primary_npc_name}'s voice memo text relevant to this scene",
    "duration": "0:35",
    "tone": "professional"
  }},
  "extra": {{}}
}}"""

    llm = get_llm(model="llama-3.1-8b-instant", temperature=0.6)

    try:
        logger.info(f"[llm-prompt] {prompt}")
        response = await acall_llm_with_retry(
            llm,
            [SystemMessage(content=prompt)]
        )
        raw = response.content.strip()
        # Also strip manually in case stop sequence didn't catch it
        raw = raw.replace("```json", "").replace("```", "").strip()
        scene = json.loads(raw)

        if scene_number >= 4:
            scene["is_final_scene"] = True

        # Post-process PM domain keys to completely remove them instead of sending nulls
        if domain == "product_manager" and "context_data" in scene:
            if scene_number == 1:
                scene["context_data"].pop("prd_data", None)
            elif scene_number == 2:
                scene["context_data"].pop("sprint_board", None)

        logger.info(f"[LLM_OK] scenario_node → scene {scene_number} generated from LLM for {domain}")
        logger.info(f"[LLM_RESPONSE] scenario_node scene {scene_number} ({domain}): {raw}")
        return {"current_scene": scene, "is_final_scene": scene.get("is_final_scene", False)}
    except Exception as e:
        logger.warning(
            f"[LLM_FALLBACK] scenario_node scene {scene_number} ({domain}) → using static "
            f"fallback scene (reason: {e})"
        )
        fallback = _fallback_scene(scene_number, domain, difficulty)
        return {"current_scene": fallback, "is_final_scene": fallback["is_final_scene"]}
