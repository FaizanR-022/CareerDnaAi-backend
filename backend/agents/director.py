"""
Simulation Director — LangGraph Implementation v2
Career Simulator · Folio3 Internship Project
-----------------------------------------------
Changes from v1:
  - Scenarios loaded from JSON files (backend/scenarios/{domain}/)
  - NPC characters loaded from JSON files
  - No hardcoded scenario config
  - Provider abstraction supports groq + openrouter
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Annotated, Any, Literal, Optional
from typing_extensions import TypedDict

from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

# ─── PATHS ───────────────────────────────────────────────────────────────────
BACKEND_DIR = Path(__file__).parent.parent          # backend/
SCENARIOS_DIR = BACKEND_DIR / "scenarios"           # backend/scenarios/


# ─── SCENARIO + NPC LOADING ──────────────────────────────────────────────────

def load_scenario(domain: str, scene_id: str) -> dict:
    """
    Load a scene config from backend/scenarios/{domain}/{scene_id}.json
    Falls back to empty dict if file not found — simulation continues in degraded mode.
    """
    path = SCENARIOS_DIR / domain / f"{scene_id}.json"
    if path.exists():
        with open(path, "r") as f:
            return json.load(f)
    print(f"[Director] WARNING: scenario file not found: {path}")
    return {}


def load_npc(domain: str, npc_id: str) -> dict:
    """
    Load NPC config from backend/scenarios/{domain}/{npc_id}.json
    """
    path = SCENARIOS_DIR / domain / f"{npc_id}.json"
    if path.exists():
        with open(path, "r") as f:
            return json.load(f)
    print(f"[Director] WARNING: NPC file not found: {path}")
    return {}


def load_full_scenario_config(domain: str) -> dict:
    """
    Load all scenes for a domain into a single config dict.
    Returns: { "domain": str, "scenes": { scene_id: scene_config }, "npcs": { npc_id: npc_config } }
    """
    domain_path = SCENARIOS_DIR / domain
    config = {"domain": domain, "scenes": {}, "npcs": {}}

    if not domain_path.exists():
        print(f"[Director] WARNING: No scenario directory for domain: {domain}")
        return config

    for file in domain_path.glob("scene_*.json"):
        scene = json.load(open(file))
        config["scenes"][scene["scene_id"]] = scene

    for file in domain_path.glob("*.json"):
        if not file.name.startswith("scene_"):
            npc = json.load(open(file))
            if "npc_id" in npc:
                config["npcs"][npc["npc_id"]] = npc

    # Attach difficulty_thresholds from first scene for easy access
    first_scene = next(iter(config["scenes"].values()), {})
    config["difficulty_thresholds"] = first_scene.get("score_thresholds", {"stretch": 75, "support": 40})

    return config


# ─── LLM SETUP ───────────────────────────────────────────────────────────────

def get_llm(model: str = "llama-3.3-70b-versatile", temperature: float = 0.3):
    """
    Provider abstraction. Set LLM_PROVIDER env var to switch.
    Supported: groq, openrouter
    """
    provider = os.getenv("LLM_PROVIDER", "groq")

    if provider == "groq":
        return ChatGroq(
            model=model,
            temperature=temperature,
            api_key=os.getenv("GROQ_API_KEY", ""),
        )
    elif provider == "openrouter":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=model,
            temperature=temperature,
            openai_api_key=os.getenv("OPENROUTER_API_KEY", ""),
            openai_api_base="https://openrouter.ai/api/v1",
        )
    else:
        raise ValueError(f"Unknown LLM_PROVIDER: {provider}. Use 'groq' or 'openrouter'.")


# ─── STATE ───────────────────────────────────────────────────────────────────

class SimulationState(TypedDict):
    # Session identity
    session_id: str
    user_id: str
    domain: str
    difficulty: str

    # Scene tracking
    current_scene_id: str
    scenes_completed: list[str]
    session_status: str

    # Simulation meters
    sprint_progress: int
    time_remaining: Optional[int]

    # Stakeholder trust  e.g. {"sara_khan": 72}
    stakeholder_trust: dict[str, int]

    # 5-dimension scores
    scores: dict[str, float]
    decisions_log: list[dict]

    # NPC compressed memory
    npc_states: dict[str, dict]

    # Current action
    user_action: str
    action_type: str

    # Response fields
    npc_response: Optional[str]
    score_update: Optional[dict]
    next_scene_id: Optional[str]
    ui_events: list[dict]

    # Scenario config (loaded at session start, read-only)
    scenario_config: dict
    user_profile: dict


# ─── NODES ───────────────────────────────────────────────────────────────────

def classify_node(state: SimulationState) -> dict:
    """Deterministic routing — no LLM. Sets action_type."""
    action = state["user_action"].lower().strip()

    if action == "__scene_complete__":
        action_type = "scene_complete"
    elif any(kw in action for kw in ["?", "clarify", "what do you mean", "can you explain",
                                      "more detail", "which", "what's the", "what is the",
                                      "tell me more", "could you"]):
        action_type = "npc_message_clarification"
    elif any(kw in action for kw in ["next sprint", "push back", "not this sprint",
                                      "defer", "push to", "move to next"]):
        action_type = "branch_decision_defer"
    elif any(kw in action for kw in ["cut", "remove", "drop ticket", "reduce scope",
                                      "remove ticket", "let's cut", "we can cut"]):
        action_type = "branch_decision_cut"
    elif any(kw in action for kw in ["yes", "add it", "let's do it", "sure", "ok",
                                      "okay", "sounds good", "let's add", "go ahead"]):
        action_type = "branch_decision_accept_blindly"
    elif any(kw in action for kw in ["escalate", "check with", "ask rayan", "loop in",
                                      "bring in", "consult"]):
        action_type = "branch_decision_escalate"
    else:
        action_type = "npc_message_general"

    print(f"[Director] classify_node → {action_type}")
    return {
        "action_type": action_type,
        "npc_response": None,
        "score_update": None,
        "next_scene_id": None,
        "ui_events": [],
    }


def score_node(state: SimulationState) -> dict:
    """LLM-as-judge scoring. Constrained JSON output."""
    llm = get_llm(model="llama-3.3-70b-versatile", temperature=0.1)

    scene_config = state["scenario_config"]["scenes"].get(state["current_scene_id"], {})
    branch_points = scene_config.get("branch_points", {})
    # Use first available branch point rubric
    rubric = next(iter(branch_points.values()), {}) if branch_points else {}
    difficulty_mod = scene_config.get("difficulty_modifiers", {}).get(state["difficulty"], {})

    prompt = f"""You are a scoring judge for a career simulation. Evaluate this student action.
Return ONLY valid JSON. No preamble, no explanation, no markdown.

DOMAIN: {state['domain']}
DIFFICULTY: {state['difficulty']}
STUDENT ACTION: "{state['user_action']}"
ACTION TYPE: {state['action_type']}
SCENE: {scene_config.get('title', 'Unknown')}
SCENE CONTEXT: {scene_config.get('description', '')}
RUBRIC DIMENSIONS: {rubric.get('dimensions', ['ambiguity_tolerance', 'communication_clarity', 'stakeholder_management'])}
GOOD SIGNALS: {rubric.get('good_signals', [])}
BAD SIGNALS: {rubric.get('bad_signals', [])}

Return exactly this JSON schema:
{{
  "overall_score": <integer 0-100>,
  "dimension_scores": {{
    "analytical_reasoning": <integer 0-100>,
    "ambiguity_tolerance": <integer 0-100>,
    "communication_clarity": <integer 0-100>,
    "attention_to_detail": <integer 0-100>,
    "decisiveness": <integer 0-100>
  }},
  "behavioural_flags": [<strings from: "clarification_sought", "escalated", "rushed", "data_backed", "vague", "accepted_blindly", "stakeholder_aware">],
  "one_line_justification": "<max 20 words>"
}}"""

    try:
        response = llm.invoke([SystemMessage(content=prompt)])
        raw = response.content.strip().replace("```json", "").replace("```", "").strip()
        score_data = json.loads(raw)
    except Exception as e:
        print(f"[Director] score_node parse error: {e}")
        score_data = {
            "overall_score": 50,
            "dimension_scores": {
                "analytical_reasoning": 50, "ambiguity_tolerance": 50,
                "communication_clarity": 50, "attention_to_detail": 50, "decisiveness": 50
            },
            "behavioural_flags": ["parse_error"],
            "one_line_justification": "Score defaulted due to parse error.",
        }

    # Update running scores (rolling average)
    updated_scores = dict(state["scores"])
    for dim, val in score_data.get("dimension_scores", {}).items():
        prev = updated_scores.get(dim, 0.0)
        updated_scores[dim] = round((prev + val) / 2, 1) if prev > 0 else float(val)

    # Append to decisions log
    updated_log = list(state["decisions_log"])
    updated_log.append({
        "scene_id": state["current_scene_id"],
        "action": state["user_action"],
        "action_type": state["action_type"],
        "score": score_data["overall_score"],
        "dimension_scores": score_data.get("dimension_scores", {}),
        "flags": score_data.get("behavioural_flags", []),
        "justification": score_data.get("one_line_justification", ""),
    })

    print(f"[Director] score_node → {score_data['overall_score']}/100 | flags: {score_data.get('behavioural_flags')}")

    return {
        "scores": updated_scores,
        "decisions_log": updated_log,
        "score_update": score_data,
        "ui_events": state["ui_events"] + [{"type": "score_update", "data": score_data}],
    }


def npc_node(state: SimulationState) -> dict:
    """LLM NPC dialogue generation. Character-constrained."""
    llm = get_llm(model="llama-3.3-70b-versatile", temperature=0.7)

    scene_config = state["scenario_config"]["scenes"].get(state["current_scene_id"], {})
    # Resolve active NPC from scene config (falls back to sara_khan if not set)
    active_npc_id = scene_config.get("active_npcs", ["sara_khan"])[0]
    npc_config = state["scenario_config"].get("npcs", {}).get(active_npc_id, {})
    npc_memory = state["npc_states"].get(active_npc_id, {
        "last_interaction_summary": "No prior interaction.",
        "relationship_score": 50,
        "current_sentiment": "neutral",
        "key_events_memory": []
    })

    # Sprint state from scene config
    sprint = scene_config.get("sprint_board", {})
    sprint_capacity = sprint.get("capacity", "unknown")
    sprint_used = len(sprint.get("tickets", []))
    sprint_available = sprint.get("available_points", 0)

    # Hard constraints — built from live state, NPC CANNOT contradict these
    hard_constraints = f"""
FACTS YOU MUST NOT CONTRADICT (these are ground truth — never override them):
- Sprint has {sprint_capacity} ticket slots maximum
- Sprint currently has {sprint_used} tickets
- Sprint has {sprint_available} spare capacity
- You do NOT know the student is being assessed or scored
- You do NOT know this is a simulation
- You do NOT know about any scoring system
"""

    personality = npc_config.get("personality", {})
    system_prompt = f"""You are {npc_config.get('name', 'Sara')}, {npc_config.get('role', 'a colleague')}.

PERSONALITY: {personality.get('summary', '')}
YOUR GOAL: {npc_config.get('goal', '')}
RELATIONSHIP TRUST: {npc_memory.get('relationship_score', 50)}/100
CURRENT MOOD: {npc_memory.get('current_sentiment', 'neutral')}
RECENT CONTEXT: {npc_memory.get('last_interaction_summary', 'No prior interaction.')}
DIFFICULTY: {state['difficulty']}

{hard_constraints}

RULES:
- Stay in character at all times. Never break the fourth wall.
- Never reveal you are an AI, a character, or part of a simulation.
- Keep response to 2-4 sentences maximum.
- If trust is below 30, be noticeably cooler and more formal.
- If trust is above 70, be warmer and more collaborative.
- Match urgency to difficulty: easy=friendly, medium=professional, hard=pressured.
"""

    try:
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"The PM said or did: {state['user_action']}\n\nRespond in character as {npc_config.get('name', 'Sara')}.")
        ])
        dialogue = response.content.strip()
    except Exception as e:
        print(f"[Director] npc_node LLM error: {e}")
        dialogue = "Got it, I'll wait to hear back from you."

    # Update NPC memory
    updated_memory = dict(npc_memory)
    updated_memory["last_interaction_summary"] = f"PM said: '{state['user_action'][:80]}'. Responded about the referral feature request."

    # Trust changes based on action type
    trust_changes = {
        "npc_message_clarification": 5,
        "branch_decision_defer": -5,
        "branch_decision_cut": 2,
        "branch_decision_accept_blindly": 10,
        "branch_decision_escalate": -2,
        "npc_message_general": 0,
    }
    trust_delta = trust_changes.get(state["action_type"], 0)
    updated_memory["relationship_score"] = max(0, min(100, npc_memory.get("relationship_score", 50) + trust_delta))
    updated_memory["current_sentiment"] = (
        "positive" if updated_memory["relationship_score"] > 65
        else "negative" if updated_memory["relationship_score"] < 35
        else "neutral"
    )

    # Add to key events if significant
    if state["action_type"].startswith("branch_decision"):
        events = list(updated_memory.get("key_events_memory", []))
        events.append({
            "event_type": state["action_type"],
            "summary": state["user_action"][:60],
            "scene_id": state["current_scene_id"]
        })
        updated_memory["key_events_memory"] = events[-5:]  # keep last 5

    updated_npc_states = dict(state["npc_states"])
    updated_npc_states[active_npc_id] = updated_memory

    updated_trust = dict(state["stakeholder_trust"])
    updated_trust[active_npc_id] = updated_memory["relationship_score"]

    print(f"[Director] npc_node → Sara responds | trust now: {updated_memory['relationship_score']}")

    return {
        "npc_response": dialogue,
        "npc_states": updated_npc_states,
        "stakeholder_trust": updated_trust,
        "ui_events": state["ui_events"] + [
            {"type": "npc_message", "npc_id": active_npc_id, "npc_name": npc_config.get("name", "Sara"), "dialogue": dialogue},
            {"type": "trust_update", "npc_id": active_npc_id, "value": updated_memory["relationship_score"]},
        ],
    }


def scene_transition_node(state: SimulationState) -> dict:
    """Deterministic scene selection. No LLM."""
    config = state["scenario_config"]
    scene_config = config["scenes"].get(state["current_scene_id"], {})
    thresholds = scene_config.get("score_thresholds", {"stretch": 75, "support": 40})
    next_scenes = scene_config.get("next_scenes", {})

    scores = state["scores"]
    avg_score = sum(v for v in scores.values() if v > 0) / max(1, sum(1 for v in scores.values() if v > 0))

    if avg_score >= thresholds.get("stretch", 75):
        next_scene_id = next_scenes.get("stretch", next_scenes.get("standard"))
        variant = "stretch"
    elif avg_score <= thresholds.get("support", 40):
        next_scene_id = next_scenes.get("support", next_scenes.get("standard"))
        variant = "support"
    else:
        next_scene_id = next_scenes.get("standard")
        variant = "standard"

    updated_completed = list(state["scenes_completed"]) + [state["current_scene_id"]]

    # Check if next scene exists
    if not next_scene_id or next_scene_id not in config.get("scenes", {}):
        print(f"[Director] scene_transition_node → SIMULATION COMPLETE (avg: {avg_score:.1f})")
        return {
            "scenes_completed": updated_completed,
            "session_status": "simulation_complete",
            "next_scene_id": None,
            "ui_events": state["ui_events"] + [{"type": "simulation_complete", "avg_score": round(avg_score, 1)}],
        }

    print(f"[Director] scene_transition_node → {next_scene_id} ({variant}, avg: {avg_score:.1f})")
    return {
        "scenes_completed": updated_completed,
        "current_scene_id": next_scene_id,
        "session_status": "scene_complete",
        "next_scene_id": next_scene_id,
        "ui_events": state["ui_events"] + [
            {"type": "scene_transition", "next_scene_id": next_scene_id, "variant": variant, "avg_score": round(avg_score, 1)}
        ],
    }


# ─── ROUTING ─────────────────────────────────────────────────────────────────

def route_after_classify(state: SimulationState) -> Literal["score_node", "npc_node", "scene_transition_node"]:
    action_type = state["action_type"]
    if action_type == "scene_complete":
        return "scene_transition_node"
    elif action_type.startswith("branch_decision"):
        return "score_node"
    else:
        return "npc_node"


def route_after_score(state: SimulationState) -> Literal["npc_node", "scene_transition_node"]:
    if state["action_type"] == "branch_decision_accept_blindly":
        return "scene_transition_node"
    return "npc_node"


# ─── GRAPH ───────────────────────────────────────────────────────────────────

def build_director():
    graph = StateGraph(SimulationState)
    graph.add_node("classify_node", classify_node)
    graph.add_node("score_node", score_node)
    graph.add_node("npc_node", npc_node)
    graph.add_node("scene_transition_node", scene_transition_node)
    graph.set_entry_point("classify_node")
    graph.add_conditional_edges("classify_node", route_after_classify, {
        "score_node": "score_node",
        "npc_node": "npc_node",
        "scene_transition_node": "scene_transition_node",
    })
    graph.add_conditional_edges("score_node", route_after_score, {
        "npc_node": "npc_node",
        "scene_transition_node": "scene_transition_node",
    })
    graph.add_edge("npc_node", END)
    graph.add_edge("scene_transition_node", END)
    return graph.compile()


# ─── INITIAL STATE ────────────────────────────────────────────────────────────

def create_initial_state(session_id: str, user_id: str, domain: str = "pm", difficulty: str = "medium") -> SimulationState:
    """
    Creates fresh session state.
    Loads scenario config from JSON files in backend/scenarios/{domain}/
    """
    scenario_config = load_full_scenario_config(domain)
    first_scene_id = "scene_1"

    # Load initial NPC trust values from NPC files
    stakeholder_trust = {}
    npc_states = {}
    for npc_id, npc_config in scenario_config.get("npcs", {}).items():
        initial_trust = npc_config.get("relationship", {}).get("initial_trust", 50)
        stakeholder_trust[npc_id] = initial_trust
        npc_states[npc_id] = {
            "last_interaction_summary": "No prior interaction.",
            "relationship_score": initial_trust,
            "current_sentiment": npc_config.get("relationship", {}).get("sentiment_on_load", "neutral"),
            "key_events_memory": []
        }

    return SimulationState(
        session_id=session_id,
        user_id=user_id,
        domain=domain,
        difficulty=difficulty,
        current_scene_id=first_scene_id,
        scenes_completed=[],
        session_status="active",
        sprint_progress=0,
        time_remaining=None,
        stakeholder_trust=stakeholder_trust,
        scores={
            "analytical_reasoning": 0.0,
            "ambiguity_tolerance": 0.0,
            "communication_clarity": 0.0,
            "attention_to_detail": 0.0,
            "decisiveness": 0.0,
        },
        decisions_log=[],
        npc_states=npc_states,
        user_action="",
        action_type="",
        npc_response=None,
        score_update=None,
        next_scene_id=None,
        ui_events=[],
        scenario_config=scenario_config,
        user_profile={"user_id": user_id},
    )
