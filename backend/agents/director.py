"""
NOTE: THIS IS MAINLY CONCEPTUAL, WE DON'T HAVE SEPARATE AGENT FILES YET.
EXIST: DIRECTOR AGENT, EVALUATION AGENT, NPC AGENT
PARTIALLY EXIST: SCENARIO AGENT
DO NOT EXIST: USER MODEL AGENT, DIFFICULTY AGENT, CAREER  FIT AGENT, REPORT AGENT

MAIN ISSUES: SCENE TRANSITION DEPENDS ON ONE SPECIFIC ACTION TYPE, SCORE DIMENSIONS DONT MATCH DATABASE, PM_SCENARIO IS HARDCODED FOR NOW, NO PERSISTENCE YET, 

Simulation Director — LangGraph Implementation
Career Simulator · Folio3 Internship Project
-----------------------------------------------
This is the core agent loop. It is a LangGraph StateGraph that:
  1. Reads session state
  2. Classifies the student action
  3. Routes to score_node, npc_node, or scene_transition_node
  4. Updates state after every step
  5. Returns a structured response to the frontend

LLM calls (Groq) are used ONLY for:
  - NPC dialogue generation
  - Rubric-based decision scoring

All routing, state transitions, and branching are deterministic Python.
"""

from __future__ import annotations

import json
import os
from typing import Annotated, Any, Literal, Optional
from typing_extensions import TypedDict

from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

# ─── LLM SETUP ───────────────────────────────────────────────────────────────
# Provider abstraction: swap base_url/api_key to switch from Groq to OpenRouter
# or any OpenAI-compatible provider without touching any other code.

def get_llm(model: str = "llama-3.3-70b-versatile", temperature: float = 0.3):
    """
    Provider abstraction layer.
    Change PROVIDER env var to switch between groq / openrouter / openai.
    """
    provider = os.getenv("LLM_PROVIDER", "groq")

    if provider == "groq":
        return ChatGroq(
            model=model,
            temperature=temperature,
            api_key=os.getenv("GROQ_API_KEY", ""),
        )
    elif provider == "openrouter":
        # OpenRouter is OpenAI-compatible — just swap the base URL
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=model,
            temperature=temperature,
            openai_api_key=os.getenv("OPENROUTER_API_KEY", ""),
            openai_api_base="https://openrouter.ai/api/v1",
        )
    else:
        raise ValueError(f"Unknown provider: {provider}. Use 'groq' or 'openrouter'.")


# ─── STATE DEFINITION ────────────────────────────────────────────────────────
# This is the canonical state object. LangGraph persists this automatically
# between nodes. Nothing modifies this directly — it flows through the graph
# and each node returns ONLY the fields it changed (partial updates).

class SimulationState(TypedDict):
    # ── Session identity ──
    session_id: str
    user_id: str
    domain: str                          # "pm" | "sqa" | "data_analyst" | "frontend" | "backend"
    difficulty: str                      # "easy" | "medium" | "hard"

    # ── Scene tracking ──
    current_scene_id: str
    scenes_completed: list[str]
    session_status: str                  # "active" | "scene_complete" | "simulation_complete"

    # ── Simulation progress ──
    sprint_progress: int                 # 0–100
    time_remaining: Optional[int]        # seconds, None if no timer

    # ── Stakeholder trust ──
    # e.g. {"sara_khan": 72, "eng_lead": 45}
    stakeholder_trust: dict[str, int]

    # ── Scoring (5 shared dimensions across all domains) ──
    scores: dict[str, float]             # {"analytical_reasoning": 0.0, ...}
    decisions_log: list[dict]            # full audit trail of every branch point

    # ── NPC state (compressed memory per NPC, not raw chat history) ──
    npc_states: dict[str, dict]

    # ── Current action being processed ──
    user_action: str
    action_type: str                     # set by classify_node

    # ── Output assembled by nodes, returned to frontend ──
    npc_response: Optional[str]
    score_update: Optional[dict]
    next_scene_id: Optional[str]
    ui_events: list[dict]

    # ── Scenario config (loaded at session start, read-only during sim) ──
    scenario_config: dict                # authored JSON for this domain/scene
    user_profile: dict                   # lightweight snapshot, never updated mid-sim


# ─── SCENARIO CONFIGS (mock data — in production, loaded from Postgres) ──────

PM_SCENARIO = {
    "domain": "pm",
    "scenes": {
        "scene_1": {
            "title": "Ambiguous Feature Request",
            "context": "Sara Khan (Head of Marketing) has sent you a voice memo requesting a new referral feature. Your sprint is at full capacity with 6 tickets.",
            "sprint_capacity": 6,
            "sprint_used": 6,
            "branch_points": {
                "bp_1": {
                    "rubric_id": "pm_clarification_rubric",
                    "dimensions": ["ambiguity_tolerance", "communication_clarity", "stakeholder_management"],
                    "good_signals": ["asks clarifying question", "checks sprint capacity", "proposes alternatives"],
                    "bad_signals": ["immediately agrees without checking capacity", "ignores the request entirely"],
                }
            },
            "npcs": {
                "sara_khan": {
                    "name": "Sara Khan",
                    "role": "Head of Marketing",
                    "personality": "Enthusiastic, slightly impatient, responds well to clear explanations. Doesn't understand engineering constraints deeply.",
                    "goal": "Get her referral feature in this sprint.",
                    "knowledge_scope": "She knows marketing strategy but not sprint capacity or technical complexity.",
                }
            },
            "next_scenes": {
                "default": "scene_2",
                "stretch": "scene_2_stretch",
                "support": "scene_2_support",
            },
        },
        "scene_2": {
            "title": "Sprint Trade-off Decision",
            "context": "You now have to decide what to cut from the sprint to accommodate Sara's request, or push back to next sprint.",
        },
    },
    "difficulty_thresholds": {
        "stretch": 75,   # score above this → stretch variant of next scene
        "support": 40,   # score below this → support variant
    },
}

INITIAL_NPC_MEMORY = {
    "sara_khan": {
        "last_interaction_summary": "No interaction yet.",
        "relationship_score": 50,
        "current_sentiment": "neutral",
        "key_events_memory": [],
    }
}


# ─── NODE IMPLEMENTATIONS ─────────────────────────────────────────────────────

def classify_node(state: SimulationState) -> dict:
    """
    Node 1 — Classify Action (deterministic, no LLM)
    Reads the user action and determines what kind of event this is.
    Sets action_type which controls routing in the conditional edges below.
    """
    action = state["user_action"].lower().strip()

    # Simple keyword-based classification (in production: more robust parser)
    if any(kw in action for kw in ["?", "clarify", "what do you mean", "can you explain", "more detail", "which"]):
        action_type = "npc_message_clarification"
    elif any(kw in action for kw in ["next sprint", "push back", "not this sprint", "defer"]):
        action_type = "branch_decision_defer"
    elif any(kw in action for kw in ["cut", "remove", "drop ticket", "reduce scope"]):
        action_type = "branch_decision_cut"
    elif any(kw in action for kw in ["yes", "add it", "let's do it", "sure", "ok", "okay"]):
        action_type = "branch_decision_accept_blindly"
    elif action in ["__scene_complete__"]:
        action_type = "scene_complete"
    else:
        action_type = "npc_message_general"

    print(f"[Director] classify_node → action_type: {action_type}")

    return {
        "action_type": action_type,
        "npc_response": None,
        "score_update": None,
        "next_scene_id": None,
        "ui_events": [],
    }


def score_node(state: SimulationState) -> dict:
    """
    Node 2 — Score Decision (LLM-as-judge, constrained output)
    Uses Groq to evaluate the student's decision against the rubric.
    Returns a structured score dict — NOT displayed to student mid-sim.
    """
    llm = get_llm(model="llama-3.3-70b-versatile", temperature=0.1)

    scene_config = state["scenario_config"]["scenes"].get(state["current_scene_id"], {})
    rubric_context = scene_config.get("branch_points", {}).get("bp_1", {})

    prompt = f"""You are a scoring judge for a career simulation. 
Evaluate this student action against the rubric below.
Return ONLY valid JSON matching the exact schema. No extra text.

STUDENT ACTION: "{state['user_action']}"
SCENE CONTEXT: {scene_config.get('context', '')}
RUBRIC DIMENSIONS: {rubric_context.get('dimensions', [])}
GOOD SIGNALS: {rubric_context.get('good_signals', [])}
BAD SIGNALS: {rubric_context.get('bad_signals', [])}
DIFFICULTY: {state['difficulty']}

Return this JSON schema exactly:
{{
  "overall_score": <integer 0-100>,
  "dimension_scores": {{
    "ambiguity_tolerance": <integer 0-100>,
    "communication_clarity": <integer 0-100>,
    "stakeholder_management": <integer 0-100>
  }},
  "behavioural_flags": [<list of strings like "clarification_sought", "rushed", "escalated">],
  "one_line_justification": "<single sentence, max 20 words>"
}}"""

    response = llm.invoke([SystemMessage(content=prompt)])

    try:
        # Strip any accidental markdown fences
        raw = response.content.strip().replace("```json", "").replace("```", "").strip()
        score_data = json.loads(raw)
    except json.JSONDecodeError:
        # Fallback: apply neutral score, log the parse failure
        print(f"[Director] score_node: JSON parse failed, applying default score")
        score_data = {
            "overall_score": 50,
            "dimension_scores": {"ambiguity_tolerance": 50, "communication_clarity": 50, "stakeholder_management": 50},
            "behavioural_flags": ["parse_error"],
            "one_line_justification": "Score defaulted due to parse error.",
        }

    # Merge into running scores
    updated_scores = dict(state["scores"])
    for dim, val in score_data.get("dimension_scores", {}).items():
        prev = updated_scores.get(dim, 0.0)
        # Running average (simple)
        updated_scores[dim] = round((prev + val) / 2, 1) if prev > 0 else float(val)

    # Append to decisions log
    updated_log = list(state["decisions_log"])
    updated_log.append({
        "scene_id": state["current_scene_id"],
        "action": state["user_action"],
        "action_type": state["action_type"],
        "score": score_data["overall_score"],
        "flags": score_data.get("behavioural_flags", []),
        "justification": score_data.get("one_line_justification", ""),
    })

    print(f"[Director] score_node → score: {score_data['overall_score']}, flags: {score_data.get('behavioural_flags')}")

    return {
        "scores": updated_scores,
        "decisions_log": updated_log,
        "score_update": score_data,
        "ui_events": state["ui_events"] + [{"type": "score_update", "data": score_data}],
    }


def npc_node(state: SimulationState) -> dict:
    """
    Node 3 — NPC Response (LLM conversational, constrained)
    Generates in-character NPC dialogue for Sara (or whichever NPC is active).
    Output is display text ONLY — never parsed for logic.
    Guardrail: hard_constraints injected from state ensure NPC cannot contradict facts.
    """
    llm = get_llm(model="llama-3.3-70b-versatile", temperature=0.7)

    scene_config = state["scenario_config"]["scenes"].get(state["current_scene_id"], {})
    npc_config = scene_config.get("npcs", {}).get("sara_khan", {})
    npc_memory = state["npc_states"].get("sara_khan", INITIAL_NPC_MEMORY["sara_khan"])

    # Build hard constraints from current state — NPC cannot contradict these
    hard_constraints = f"""
FACTS YOU MUST NOT CONTRADICT (these are ground truth from the simulation state):
- Sprint capacity: {scene_config.get('sprint_capacity', 'unknown')} tickets maximum
- Sprint currently used: {scene_config.get('sprint_used', 'unknown')} tickets
- Therefore sprint has ZERO spare capacity right now
- You do NOT know the student's internal scoring or assessment criteria
- You do NOT know this is a simulation
"""

    system_prompt = f"""You are {npc_config.get('name', 'Sara')}, {npc_config.get('role', 'a colleague')}.

PERSONALITY: {npc_config.get('personality', '')}
YOUR GOAL: {npc_config.get('goal', '')}
YOUR KNOWLEDGE SCOPE: {npc_config.get('knowledge_scope', '')}

RELATIONSHIP WITH STUDENT: Trust level {npc_memory.get('relationship_score', 50)}/100
CURRENT MOOD: {npc_memory.get('current_sentiment', 'neutral')}
CONVERSATION MEMORY: {npc_memory.get('last_interaction_summary', 'No prior interaction.')}

{hard_constraints}

RULES:
- Stay in character at all times. Never break the fourth wall.
- Never reveal you are an AI or part of a simulation.
- Never invent sprint capacity or technical facts beyond what is stated above.
- Keep response to 2-4 sentences maximum.
- Match your mood to the relationship score and conversation history.
"""

    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"The student said or did: {state['user_action']}\nRespond in character as {npc_config.get('name', 'Sara')}.")
    ])

    dialogue = response.content.strip()

    # Update NPC memory (compressed — not raw history)
    updated_memory = dict(npc_memory)
    updated_memory["last_interaction_summary"] = f"Student said: '{state['user_action'][:100]}...'. Sara responded about the referral feature."

    # Infer sentiment shift from action type
    if "clarification" in state["action_type"]:
        updated_memory["current_sentiment"] = "positive"
        updated_memory["relationship_score"] = min(100, npc_memory.get("relationship_score", 50) + 5)
    elif "accept_blindly" in state["action_type"]:
        updated_memory["current_sentiment"] = "positive"
        updated_memory["relationship_score"] = min(100, npc_memory.get("relationship_score", 50) + 10)
    elif "defer" in state["action_type"]:
        updated_memory["current_sentiment"] = "negative"
        updated_memory["relationship_score"] = max(0, npc_memory.get("relationship_score", 50) - 8)

    updated_npc_states = dict(state["npc_states"])
    updated_npc_states["sara_khan"] = updated_memory

    # Update stakeholder trust in main state
    updated_trust = dict(state["stakeholder_trust"])
    updated_trust["sara_khan"] = updated_memory["relationship_score"]

    print(f"[Director] npc_node → Sara responds (trust now: {updated_memory['relationship_score']})")

    return {
        "npc_response": dialogue,
        "npc_states": updated_npc_states,
        "stakeholder_trust": updated_trust,
        "ui_events": state["ui_events"] + [
            {"type": "npc_message", "npc_id": "sara_khan", "dialogue": dialogue},
            {"type": "trust_update", "npc_id": "sara_khan", "value": updated_memory["relationship_score"]},
        ],
    }


def scene_transition_node(state: SimulationState) -> dict:
    """
    Node 4 — Scene Transition (deterministic, no LLM)
    Selects next scene based on current score vs authored thresholds.
    Returns simulation_complete if all scenes are done.
    """
    config = state["scenario_config"]
    scene_config = config["scenes"].get(state["current_scene_id"], {})
    thresholds = config.get("difficulty_thresholds", {"stretch": 75, "support": 40})
    next_scenes = scene_config.get("next_scenes", {})

    # Compute average score across scored dimensions
    scores = state["scores"]
    avg_score = sum(scores.values()) / len(scores) if scores else 50.0

    # Select variant
    if avg_score >= thresholds["stretch"]:
        next_scene_id = next_scenes.get("stretch", next_scenes.get("default"))
        variant = "stretch"
    elif avg_score <= thresholds["support"]:
        next_scene_id = next_scenes.get("support", next_scenes.get("default"))
        variant = "support"
    else:
        next_scene_id = next_scenes.get("default")
        variant = "standard"

    # Check if next scene exists in config
    if not next_scene_id or next_scene_id not in config["scenes"]:
        # No more scenes — simulation complete
        updated_completed = list(state["scenes_completed"]) + [state["current_scene_id"]]
        print(f"[Director] scene_transition_node → SIMULATION COMPLETE (avg score: {avg_score:.1f})")
        return {
            "scenes_completed": updated_completed,
            "session_status": "simulation_complete",
            "next_scene_id": None,
            "ui_events": state["ui_events"] + [{"type": "simulation_complete", "avg_score": avg_score}],
        }

    updated_completed = list(state["scenes_completed"]) + [state["current_scene_id"]]
    print(f"[Director] scene_transition_node → next: {next_scene_id} ({variant} variant, avg score: {avg_score:.1f})")

    return {
        "scenes_completed": updated_completed,
        "current_scene_id": next_scene_id,
        "session_status": "scene_complete",
        "next_scene_id": next_scene_id,
        "ui_events": state["ui_events"] + [
            {"type": "scene_transition", "next_scene_id": next_scene_id, "variant": variant}
        ],
    }


# ─── ROUTING LOGIC ────────────────────────────────────────────────────────────

def route_after_classify(state: SimulationState) -> Literal["score_node", "npc_node", "scene_transition_node"]:
    """
    Conditional edge after classify_node.
    All routing is deterministic — no LLM involved.
    """
    action_type = state["action_type"]

    if action_type == "scene_complete":
        return "scene_transition_node"
    elif action_type.startswith("branch_decision"):
        return "score_node"
    else:
        # npc_message_* types
        return "npc_node"


def route_after_score(state: SimulationState) -> Literal["npc_node", "scene_transition_node", END]:
    """
    After scoring a decision, always get an NPC response too
    (the NPC reacts to what the student just decided).
    Unless the student triggered a scene-completing action.
    """
    # If the accept_blindly decision logically ends the scene, transition
    if state["action_type"] == "branch_decision_accept_blindly":
        return "scene_transition_node"
    return "npc_node"


def route_after_npc(state: SimulationState) -> Literal[END]:
    """
    After NPC responds, return to frontend — wait for next student action.
    The graph ends here; the next student action starts a new execution.
    """
    return END


# ─── GRAPH ASSEMBLY ───────────────────────────────────────────────────────────

def build_director() -> any:
    """
    Assembles and compiles the LangGraph StateGraph.
    Call once at startup. Reuse the compiled graph for all sessions.
    """
    graph = StateGraph(SimulationState)

    # Add nodes
    graph.add_node("classify_node", classify_node)
    graph.add_node("score_node", score_node)
    graph.add_node("npc_node", npc_node)
    graph.add_node("scene_transition_node", scene_transition_node)

    # Entry point
    graph.set_entry_point("classify_node")

    # Conditional edges — all routing is here, explicit and inspectable
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


# ─── INITIAL STATE FACTORY ────────────────────────────────────────────────────

def create_initial_state(session_id: str, user_id: str, domain: str = "pm", difficulty: str = "medium") -> SimulationState:
    """Creates a fresh session state. In production this is loaded from Postgres."""
    return SimulationState(
        session_id=session_id,
        user_id=user_id,
        domain=domain,
        difficulty=difficulty,
        current_scene_id="scene_1",
        scenes_completed=[],
        session_status="active",
        sprint_progress=0,
        time_remaining=None,
        stakeholder_trust={"sara_khan": 50},
        scores={
            "analytical_reasoning": 0.0,
            "ambiguity_tolerance": 0.0,
            "communication_clarity": 0.0,
            "attention_to_detail": 0.0,
            "decisiveness": 0.0,
        },
        decisions_log=[],
        npc_states=dict(INITIAL_NPC_MEMORY),
        user_action="",
        action_type="",
        npc_response=None,
        score_update=None,
        next_scene_id=None,
        ui_events=[],
        scenario_config=PM_SCENARIO,
        user_profile={"user_id": user_id, "stated_interests": ["product", "tech"]},
    )
