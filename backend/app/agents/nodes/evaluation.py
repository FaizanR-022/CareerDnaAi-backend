"""
evaluation_node — LLM-as-judge scoring
One Groq call per invocation. Returns EvaluationResult dict.
Uses few-shot anchoring for consistent scoring baseline.
Stop sequence enforces clean JSON output.
Never raises exceptions.
"""
import json
import logging
from app.agents.llm import get_llm
from app.agents.state import SimulationState
from langchain_core.messages import SystemMessage

logger = logging.getLogger(__name__)

# FEW-SHOT ANCHORS — injected into every PM evaluation prompt
PM_FEW_SHOT = """
=== FEW-SHOT SCORING EXAMPLES ===

EXAMPLE 1 — Strong response (score ~85):
Scene: Sara asks for referral feature, sprint at full capacity (0 spare)
Student response: "Sara, before I commit to this, can you help me understand
what success looks like for the referral feature? I want to check our sprint
capacity first and get back to you in 30 minutes with a clear answer."
Expected JSON:
{
  "overall_score": 85,
  "dimension_scores": {
    "analytical_reasoning": 80,
    "ambiguity_tolerance": 88,
    "communication_clarity": 85,
    "attention_to_detail": 78,
    "decisiveness": 82
  },
  "behavioral_flags": ["clarification_sought", "stakeholder_aware"],
  "feedback_summary": "You asked a clarifying question and set a clear timeline before committing. This shows good stakeholder management and ambiguity tolerance.",
  "justification": "Asked clarifying question, set timeline, didn't commit without checking capacity.",
  "npc_state_updates": [
    {"npc_id": "sara_khan", "trust_score": 55, "sentiment": "positive", "memory_summary": "PM asked for success metrics before committing. Positive signal."}
  ],
  "reasoning": "Student demonstrated appropriate PM behavior by seeking clarification before committing to scope."
}

EXAMPLE 2 — Weak response (score ~20):
Scene: Same scene as above.
Student response: "Sure, we'll add it this sprint!"
Expected JSON:
{
  "overall_score": 20,
  "dimension_scores": {
    "analytical_reasoning": 20,
    "ambiguity_tolerance": 15,
    "communication_clarity": 35,
    "attention_to_detail": 20,
    "decisiveness": 65
  },
  "behavioral_flags": ["accepted_blindly"],
  "feedback_summary": "You committed immediately without checking sprint capacity or asking any clarifying questions. This risks overloading the team.",
  "justification": "Committed without checking capacity or asking any clarifying questions.",
  "npc_state_updates": [
    {"npc_id": "sara_khan", "trust_score": 60, "sentiment": "positive", "memory_summary": "PM agreed immediately. She's happy but PM may have overcommitted."}
  ],
  "reasoning": "Student accepted the request blindly without performing due diligence on capacity or scope."
}
=== END FEW-SHOT EXAMPLES ===
"""

def _fallback_evaluation() -> dict:
    """Returns valid EvaluationResult shape when LLM fails."""
    return {
        "overall_score": 50.0,
        "dimension_scores": {
            "analytical_reasoning": 50.0,
            "ambiguity_tolerance": 50.0,
            "communication_clarity": 50.0,
            "attention_to_detail": 50.0,
            "decisiveness": 50.0,
        },
        "behavioral_flags": ["evaluation_unavailable"],
        "feedback_summary": "Your response was recorded. Evaluation temporarily unavailable.",
        "justification": "Evaluation defaulted due to processing error.",
        "npc_state_updates": [],
        "reasoning": "Evaluation could not be completed. Default scores applied.",
        "extra": {"fallback": True},
    }

def evaluation_node(state: SimulationState) -> dict:
    """
    LangGraph node — scores student response for current scene.
    Called by: graph on evaluate_response invocation.
    Returns partial state update with current_evaluation and latest_score.
    """
    domain = state.get("domain", "product_manager")
    difficulty = state.get("difficulty", "medium")
    scene = state.get("current_scene", {})
    history = state.get("history", [])
    
    # Get the student's response from state
    # It comes in via the history — the last entry has no evaluation yet
    # Or it comes via a separate field if you set it in the invoking code
    student_response = state.get("student_response", "")
    
    if not student_response:
        logger.warning("evaluation_node called with no student_response in state")
        return {"current_evaluation": _fallback_evaluation(), "latest_score": 50.0}

    # Build history context (last 2 evaluated entries)
    history_context = ""
    evaluated = [h for h in history if h.get("evaluation")]
    if evaluated:
        last_two = evaluated[-2:]
        parts = [f"Scene {h['scene'].get('scene_number','?')}: score {h['evaluation'].get('overall_score','?')}/100" for h in last_two]
        history_context = "Prior performance: " + " | ".join(parts)
    else:
        history_context = "This is the first response — no prior history."

    # Scoring thresholds explanation for the LLM
    thresholds = """
SCORING THRESHOLDS:
- 75-100: Stretch — exceeds expectations, proactive, data-backed
- 40-74: Expected — handles situation with minor gaps  
- Below 40: Support — critical failure, triggers difficulty reduction
"""

    prompt = f"""You are an expert evaluator for a {domain.replace('_', ' ')} career simulation.
Score the student's response honestly and precisely.

{PM_FEW_SHOT}

NOW EVALUATE THIS:
Scene: {scene.get('title', 'Unknown')} — {scene.get('narrative', '')}
Domain: {domain}
Difficulty: {difficulty}
Student response: "{student_response}"
{history_context}

{thresholds}

DIMENSION SCORING GUIDE:
- analytical_reasoning: Did they think logically? Reference data? Identify root cause?
- ambiguity_tolerance: Did they handle unclear requirements well without panicking?
- communication_clarity: Was their message specific, professional, actionable?
- attention_to_detail: Did they catch constraints others miss? Read the full situation?
- decisiveness: Did they make a clear decision without being asked twice?

Return ONLY valid JSON. No markdown. No backticks. No preamble. No explanation outside the JSON:
{{
  "overall_score": <float 0-100>,
  "dimension_scores": {{
    "analytical_reasoning": <float 0-100>,
    "ambiguity_tolerance": <float 0-100>,
    "communication_clarity": <float 0-100>,
    "attention_to_detail": <float 0-100>,
    "decisiveness": <float 0-100>
  }},
  "behavioral_flags": ["clarification_sought" | "accepted_blindly" | "escalated" | "data_backed" | "vague" | "stakeholder_aware" | "rushed"],
  "feedback_summary": "2-3 sentences shown to student explaining their score",
  "justification": "one sentence max 20 words",
  "npc_state_updates": [
    {{
      "npc_id": "sara_khan",
      "trust_score": <int 0-100>,
      "sentiment": "positive" | "neutral" | "negative",
      "memory_summary": "one sentence summarizing this interaction for NPC memory"
    }}
  ],
  "reasoning": "1-2 sentences explaining why this triggers a difficulty change if score < 40",
  "extra": {{}}
}}"""

    llm = get_llm(model="llama-3.3-70b-versatile", temperature=0.1)
    
    try:
        response = llm.invoke(
            [SystemMessage(content=prompt)],
            stop=["```"]  # STOP SEQUENCE — strips markdown backticks
        )
        raw = response.content.strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        evaluation = json.loads(raw)
        latest_score = float(evaluation.get("overall_score", 50.0))
        logger.info(f"evaluation_node → {latest_score}/100 | flags: {evaluation.get('behavioral_flags')}")
        return {"current_evaluation": evaluation, "latest_score": latest_score}
    except Exception as e:
        logger.error(f"evaluation_node error: {e} | raw: {response.content[:200] if 'response' in dir() else 'no response'}")
        fallback = _fallback_evaluation()
        return {"current_evaluation": fallback, "latest_score": 50.0}
