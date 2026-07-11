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

# FEW-SHOT ANCHORS — injected into PM evaluation prompt
PM_FEW_SHOT = """
=== FEW-SHOT SCORING EXAMPLES ===

EXAMPLE 1 — Strong response (score ~88):
Scene: Head of Marketing Sara Khan demands immediate insertion of an unvetted viral referral widget into an already locked active sprint payload.
Student response: "Sara, I understand the urgency of driving viral referrals to meet our marketing OKRs. However, adding this widget to the locked active sprint payload presents a significant risk to our current delivery commitments. Before we schedule this work, I need us to pull the core engagement metrics and perform a quick impact analysis on our conversion funnels. Let's align on the expected CAC savings and prioritize this for the next planning session based on capacity bounds and strategic ROI."
Expected JSON:
{
  "overall_score": 88,
  "dimension_scores": {
    "analytical_reasoning": 90,
    "ambiguity_tolerance": 85,
    "communication_clarity": 92,
    "attention_to_detail": 85,
    "decisiveness": 88
  },
  "behavioral_flags": ["strategic_alignment", "capacity_protection"],
  "feedback_summary": "You successfully handled the marketing request without accepting it blindly. You protected the team velocity and requested metric validation first.",
  "justification": "Handles Sara's feature request via structured pushback to check metrics",
  "npc_state_updates": [
    {"npc_id": "sara_khan", "trust_score": 55, "sentiment": "neutral", "memory_summary": "PM protected sprint capacity and requested metrics before scheduling referral widget."}
  ],
  "reasoning": "Student demonstrated strong capacity protection and requested metric validation before committing."
}

EXAMPLE 2 — Weak response (score ~25):
Scene: Same scene as above.
Student response: "Sure, Sara! If marketing needs this viral referral widget immediately, we will just squeeze it into the current sprint. I will tell the engineering team to work overtime this week to get it done. We can skip the code reviews and metric validations for now; getting this live is all that matters."
Expected JSON:
{
  "overall_score": 25,
  "dimension_scores": {
    "analytical_reasoning": 20,
    "ambiguity_tolerance": 30,
    "communication_clarity": 40,
    "attention_to_detail": 15,
    "decisiveness": 20
  },
  "behavioral_flags": ["accepted_blindly", "engineering_overwork", "poor_quality_standards"],
  "feedback_summary": "You committed immediately without checking sprint capacity or asking clarifying questions. This risks overloading the team and degrading quality.",
  "justification": "Blindly overcommits engineers to overwork",
  "npc_state_updates": [
    {"npc_id": "sara_khan", "trust_score": 60, "sentiment": "positive", "memory_summary": "PM agreed immediately to squeeze in the referral widget."}
  ],
  "reasoning": "Student blindly committed to marketing scope without analytical verification or capacity checks."
}
=== END FEW-SHOT EXAMPLES ===
"""

# FEW-SHOT ANCHORS — injected into SQA evaluation prompt
SQA_FEW_SHOT = """
=== FEW-SHOT SCORING EXAMPLES ===

EXAMPLE 1 — Strong response (score ~92):
Scene: Bug escalation to Eng Lead Dan, payment gateway timeout.
Student response: "Dan, during our regression testing of the payment flow (v2.1.0-rc2) on staging, we identified a critical error preventing successful checkout completion. The issue occurs when users select multi-currency options under slow network profiles. 

Reproduction Steps:
1. Navigate to /checkout with a cart value > $100.
2. Toggle currency selection to EUR or GBP.
3. Emulate a Fast 3G connection and click 'Pay Now'.

Observed Behavior: The transaction fails with a 504 Gateway Timeout.
Console logs and traceback reference attached: [checkout-service:line-102: ConnectionTimeoutError]. 
Impact: 100% block rate on payment processing for international test cards on staging."
Expected JSON:
{
  "overall_score": 92,
  "dimension_scores": {
    "analytical_reasoning": 95,
    "ambiguity_tolerance": 90,
    "communication_clarity": 94,
    "attention_to_detail": 95,
    "decisiveness": 86
  },
  "behavioral_flags": ["objective_evidence", "precise_reporting"],
  "feedback_summary": "You provided excellent technical details, reproduction steps, and logs. This enables the engineering team to reproduce and fix the bug immediately.",
  "justification": "Provides clear reproduction steps, logs, and objective severity data to Dan",
  "npc_state_updates": [
    {"npc_id": "dan", "trust_score": 80, "sentiment": "positive", "memory_summary": "SQA engineer filed a high-quality bug report with logs and repro steps."}
  ],
  "reasoning": "Student demonstrates high attention to detail and precise technical communication."
}

EXAMPLE 2 — Weak response (score ~30):
Scene: Bug escalation to VP of Product Zara.
Student response: "Hi VP of Product Zara, the checkout page looks completely broken and unprofessional. Some text boxes are slightly misaligned on my mobile screen, and the checkout button looks weird. This is a massive blocker for the launch and we should halt the entire release until this is fixed immediately."
Expected JSON:
{
  "overall_score": 30,
  "dimension_scores": {
    "analytical_reasoning": 25,
    "ambiguity_tolerance": 20,
    "communication_clarity": 40,
    "attention_to_detail": 30,
    "decisiveness": 35
  },
  "behavioral_flags": ["inappropriate_escalation", "subjective_reporting", "lack_of_technical_evidence"],
  "feedback_summary": "You escalated a minor alignment issue directly to executive leadership without technical evidence or reproduction steps. This creates unnecessary panic.",
  "justification": "Escalates minor UI alignment issues to executives without technical evidence",
  "npc_state_updates": [
    {"npc_id": "zara_malik", "trust_score": 40, "sentiment": "negative", "memory_summary": "SQA escalated minor UI issue directly to executive level without developer alignment."}
  ],
  "reasoning": "Student failed to follow standard triage channels and relied on subjective reports."
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

    # Choose few-shot anchors dynamically based on domain
    few_shot = SQA_FEW_SHOT if domain == "sqa_engineer" else PM_FEW_SHOT

    # Scoring thresholds explanation for the LLM
    thresholds = """
SCORING THRESHOLDS:
- 75-100: Stretch — exceeds expectations, proactive, data-backed
- 40-74: Expected — handles situation with minor gaps  
- Below 40: Support — critical failure, triggers difficulty reduction
"""

    prompt = f"""You are an expert evaluator for a {domain.replace('_', ' ')} career simulation.
Score the student's response honestly and precisely.

{few_shot}

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
