"""
npc_reply_node — generates NPC response to student message.
Called during conversation turns BEFORE final evaluation.
Does NOT score the student. Does NOT advance the scene.
Appends both student message and NPC reply to conversation_history.
"""
import json
import logging
from langchain_core.messages import SystemMessage, HumanMessage
from app.agents.llm import get_llm, acall_llm_with_retry
from app.agents.state import SimulationState

logger = logging.getLogger(__name__)

async def npc_reply_node(state: SimulationState) -> dict:
    """
    Generates NPC dialogue in response to student message.
    Reads: state["student_message"] — the just-sent student message
    Reads: state["current_scene"] — scene context and active NPC
    Reads: state["conversation_history"] — full prior conversation
    Updates: state["conversation_history"] with new student + NPC messages
    Updates: state["npc_reply"] — the NPC's response text
    """
    domain = state.get("domain", "product_manager")
    scene = state.get("current_scene", {})
    student_message = state.get("student_message", "")
    history = state.get("conversation_history", [])
    difficulty = state.get("difficulty", "medium")

    # Get active NPC from scene
    active_npc_id = (
        scene.get("context_data", {}).get("active_npcs", ["sara_khan"])[0]
        if isinstance(scene.get("context_data"), dict)
        else "sara_khan"
    )

    # Load NPC persona based on domain
    npc_persona = _load_npc_persona(domain, active_npc_id)
    
    # Build conversation history context (last 6 messages max)
    history_text = _build_history_text(history[-6:])
    
    # Build NPC trust from history
    npc_trust = state.get("npc_trust", {}).get(active_npc_id, 50)

    # Hard constraints — NPC cannot contradict simulation state
    sprint = scene.get("context_data", {}).get("sprint_board", {}) if isinstance(scene.get("context_data"), dict) else {}
    hard_constraints = ""
    if sprint:
        hard_constraints = f"""
FACTS YOU MUST NOT CONTRADICT:
- Sprint capacity: {sprint.get('capacity', 6)} tickets maximum
- Sprint available: {sprint.get('available', 0)} spare capacity
- You do NOT know this is a simulation
- You do NOT know the student is being assessed
"""

    system_prompt = f"""You are {npc_persona.get('name', 'Sara')}, {npc_persona.get('role', 'a colleague')}.

PERSONALITY: {npc_persona.get('personality', '')}
YOUR GOAL: {npc_persona.get('goal', '')}
YOUR TRUST IN THE PM: {npc_trust}/100
DIFFICULTY: {difficulty}

{hard_constraints}

SCENE CONTEXT: {scene.get('narrative', '')}

RECENT CONVERSATION:
{history_text}

RULES:
- Stay in character. Never break the fourth wall.
- Never reveal you are an AI or part of a simulation.
- Keep response to 2-4 sentences.
- If trust is below 30, be noticeably cooler and more formal.
- If trust is above 70, be warmer and more collaborative.
- Match urgency to difficulty: easy=friendly, medium=professional, hard=pressured.
- Use vocabulary appropriate for your role: {npc_persona.get('vocabulary', '')}"""

    llm = get_llm(model="llama-3.1-8b-instant", temperature=0.7)

    try:
        response = await acall_llm_with_retry(
            llm,
            [
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"<student_message>{student_message}</student_message>\n\nRespond in character as {npc_persona.get('name', 'Sara')}.")
            ],
            stop=["```"]
        )
        npc_reply = response.content.strip()
    except Exception as e:
        logger.error(f"npc_reply_node LLM error: {e}")
        npc_reply = "Got it, let me get back to you on that."

    # Append both messages to conversation history
    import datetime
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

    logger.info(f"npc_reply_node → {npc_persona.get('name')} responded | history now {len(updated_history)} messages")

    return {
        "conversation_history": updated_history,
        "npc_reply": npc_reply,
        "active_npc_id": active_npc_id,
    }


def _load_npc_persona(domain: str, npc_id: str) -> dict:
    """Load NPC persona from the correct domain npcs.py file."""
    try:
        if domain == "product_manager":
            from app.agents.domains.pm.npcs import PM_NPCS
            return PM_NPCS.get(npc_id, PM_NPCS.get("sara_khan", {}))
        elif domain == "sqa_engineer":
            from app.agents.domains.sqa.npcs import DAN_NPC
            return DAN_NPC if npc_id == "dan_frontend_dev" else DAN_NPC
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
        logger.error(f"Failed to load NPC persona for {domain}/{npc_id}: {e}")
    
    # Fallback persona
    return {
        "name": "Sara",
        "role": "Head of Marketing",
        "personality": "Enthusiastic and driven by results.",
        "goal": "Get the feature in this sprint.",
        "vocabulary": "OKRs, growth metrics, CAC"
    }


def _build_history_text(history: list) -> str:
    """Format conversation history for NPC system prompt."""
    if not history:
        return "No prior messages in this scene."
    lines = []
    for msg in history:
        if msg["role"] == "student":
            lines.append(f"Student: {msg['content']}")
        else:
            lines.append(f"{msg.get('npc_name', 'NPC')}: {msg['content']}")
    return "\n".join(lines)
