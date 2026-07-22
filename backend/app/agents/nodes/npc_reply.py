"""
npc_reply_node — NPC reply grounded in current scene context.
Sara/Dan/etc. can ONLY discuss the scene shown to the student.
They cannot invent a different scenario.
"""
import json
import logging
import datetime
from langchain_core.messages import SystemMessage, HumanMessage
from app.agents.llm import get_llm, acall_llm_with_retry
from app.agents.state import SimulationState

logger = logging.getLogger(__name__)


async def npc_reply_node(state: SimulationState) -> dict:
    domain = state.get("domain", "product_manager")
    scene = state.get("current_scene") or {}
    student_message = state.get("student_message", "")
    history = state.get("conversation_history", [])
    difficulty = state.get("difficulty", "medium")
    npc_trust_map = state.get("npc_trust", {})

    if not scene:
        logger.warning("npc_reply_node called with no current_scene in state")
        return {
            "npc_reply": "Got it, let me look into that.",
            "conversation_history": list(history) + [
                {"role": "student", "npc_id": None, "content": student_message,
                 "timestamp": datetime.datetime.utcnow().isoformat()},
                {"role": "npc", "npc_id": "unknown", "npc_name": "NPC",
                 "content": "Got it, let me look into that.",
                 "timestamp": datetime.datetime.utcnow().isoformat()}
            ],
            "active_npc_id": "unknown",
        }

    # ── Extract scene ground truth ──────────────────────────────────────────
    scene_narrative = scene.get("narrative", "")
    scene_title = scene.get("title", "")
    scene_type = scene.get("scene_type") or scene.get("context_data", {}).get("scene_type", "")
    context_data = scene.get("context_data") or {}
    prompt_for_response = scene.get("prompt_for_response", "")
    
    # Sprint board (PM domain)
    sprint_board = context_data.get("sprint_board") or {}
    sprint_capacity = sprint_board.get("capacity", "")
    sprint_available = sprint_board.get("available", 0)
    sprint_tickets = sprint_board.get("tickets", [])
    
    # PRD state (PM domain)
    prd_status = context_data.get("prd_status", "")
    
    # Active NPC
    active_npcs = context_data.get("active_npcs", [])
    active_npc_id = active_npcs[0] if active_npcs else "sara_khan"
    
    # NPC persona
    npc_persona = _load_npc_persona(domain, active_npc_id)
    npc_trust = npc_trust_map.get(active_npc_id, 50)

    # ── Scene opening messages (what student already saw) ───────────────────
    scene_messages = scene.get("messages", [])
    opening_summary = ""
    if scene_messages:
        opening_summary = "SCENE OPENING MESSAGES (what was already sent to student):\n"
        for msg in scene_messages:
            opening_summary += f"- {msg.get('sender', 'NPC')}: {msg.get('content', '')}\n"

    # ── Sprint board context (only inject if it exists) ─────────────────────
    sprint_context = ""
    if sprint_tickets:
        ticket_lines = "\n".join([
            f"  - {t.get('id','')}: {t.get('title','')} [{t.get('priority','')}] "
            f"{t.get('points','')} pts"
            for t in sprint_tickets
        ])
        sprint_context = f"""
SPRINT BOARD (ground truth — you must not contradict these):
  Capacity: {sprint_capacity} tickets maximum
  Available: {sprint_available} spare capacity (this is the REAL number, never change it)
  Current tickets:
{ticket_lines}
"""

    # ── Conversation history (last 8 messages) ──────────────────────────────
    recent_history = history[-8:] if history else []
    history_text = _format_history(recent_history) if recent_history else "No prior messages in this scene."

    # ── Build system prompt ──────────────────────────────────────────────────
    system_prompt = f"""You are {npc_persona.get('name', 'Sara')}, {npc_persona.get('role', 'a colleague')}.

━━━ SCENE CONTEXT (this is what the student sees — you must stay within this) ━━━
Scene: {scene_title}
Situation: {scene_narrative}
What the student is being asked: {prompt_for_response}

{opening_summary}
{sprint_context}
━━━ YOUR CHARACTER ━━━
Personality: {npc_persona.get('personality', '')}
Your goal in this scene: {npc_persona.get('goal', '')}
Your vocabulary: {npc_persona.get('vocabulary', '')}
Your trust in the student: {npc_trust}/100
Difficulty level: {difficulty}

━━━ ABSOLUTE CONSTRAINTS — NEVER VIOLATE ━━━
- You are discussing ONLY the situation described in "SCENE CONTEXT" above
- You are NOT discussing any other feature, project, or problem
- If the sprint board shows {sprint_available} spare capacity, you accept that as fact
- You do NOT know this is a simulation
- You do NOT know the student is being assessed or scored
- You do NOT know about any scoring system
- Never break character or acknowledge you are an AI

━━━ CONVERSATION SO FAR ━━━
{history_text}

━━━ RESPONSE RULES ━━━
- Stay STRICTLY within the scene context above
- 2-4 sentences maximum
- Trust {npc_trust}/100: {"warmer and collaborative" if npc_trust > 65 else "cooler and more formal" if npc_trust < 35 else "professional"}
- Urgency matches difficulty: {"friendly" if difficulty == "easy" else "pressured" if difficulty == "hard" else "professional"}
- Use vocabulary: {npc_persona.get('vocabulary', '')}
- NEVER say anything that contradicts the scene narrative or sprint board above"""

    llm = get_llm(model="llama-3.3-70b-versatile", temperature=0.7)

    try:
        response = await acall_llm_with_retry(
            llm,
            [
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"<student_message>{student_message}</student_message>\n\nRespond in character as {npc_persona.get('name', 'Sara')}. Stay within the scene context.")
            ],
            stop=["```"]
        )
        npc_reply = response.content.strip()
    except Exception as e:
        logger.error(f"npc_reply_node LLM error: {e}")
        npc_reply = "Let me think about that and get back to you."

    # ── Append to conversation history ───────────────────────────────────────
    ts = datetime.datetime.utcnow().isoformat()
    updated_history = list(history) + [
        {
            "role": "student",
            "npc_id": None,
            "content": student_message,
            "timestamp": ts
        },
        {
            "role": "npc",
            "npc_id": active_npc_id,
            "npc_name": npc_persona.get("name", "Sara"),
            "content": npc_reply,
            "timestamp": ts
        }
    ]

    logger.info(
        f"npc_reply_node → {npc_persona.get('name')} responded "
        f"| trust: {npc_trust} | history: {len(updated_history)} msgs"
    )

    return {
        "npc_reply": npc_reply,
        "conversation_history": updated_history,
        "active_npc_id": active_npc_id,
    }


def _load_npc_persona(domain: str, npc_id: str) -> dict:
    try:
        if domain == "product_manager":
            from app.agents.domains.pm.npcs import PM_NPCS
            return PM_NPCS.get(npc_id, list(PM_NPCS.values())[0])
        elif domain == "sqa_engineer":
            from app.agents.domains.sqa.npcs import DAN_NPC
            return DAN_NPC
        elif domain == "data_analyst":
            from app.agents.domains.da.npcs import DA_VP_NPC
            return DA_VP_NPC
        elif domain == "frontend_engineer":
            from app.agents.domains.fe.npcs import FE_CLIENT_NPC
            return FE_CLIENT_NPC
        elif domain == "backend_engineer":
            from app.agents.domains.be.npcs import BE_TEAM_LEAD_NPC
            return BE_TEAM_LEAD_NPC
    except Exception as e:
        logger.error(f"Failed to load NPC for {domain}/{npc_id}: {e}")
    return {
        "name": "Sara",
        "role": "Head of Marketing",
        "personality": "Enthusiastic, driven by growth metrics, impatient.",
        "goal": "Get the referral feature into the current sprint.",
        "vocabulary": "OKRs, growth metrics, CAC, referral features"
    }


def _format_history(history: list) -> str:
    lines = []
    for msg in history:
        if msg["role"] == "student":
            lines.append(f"Student: {msg['content']}")
        else:
            lines.append(f"{msg.get('npc_name', 'NPC')}: {msg['content']}")
    return "\n".join(lines)
