"""
graph.py — Single LangGraph graph with interrupt() for student input pause.

Flow:
  supervisor_node → scenario_node → [interrupt: wait for student]
  → evaluation_node → career_fit_node → scenario_node (loop) | report_node | END
"""

from __future__ import annotations
import logging
from typing import Any
from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt, Command
from app.agents.state import SimulationState
from app.agents.nodes.supervisor import supervisor_node
from app.agents.nodes.scenario import scenario_node
from app.agents.nodes.evaluation import evaluation_node
from app.agents.nodes.career_fit import career_fit_node
from app.agents.nodes.report import report_node
from app.schemas.agent_contracts import (
    SceneContent, SceneGenerationContext,
    EvaluationResult, EvaluationContext,
    FitReportResult, FitReportContext,
    MCQGenerationResult, MCQGenerationContext,
)

logger = logging.getLogger(__name__)

# ─── CHECKPOINTER ────────────────────────────────────────────────────────────

def _build_checkpointer():
    try:
        from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
        from app.core.config import get_settings
        settings = get_settings()
        db_url = settings.database_url
        checkpointer = AsyncPostgresSaver.from_conn_string(db_url)
        logger.info("Using PostgresSaver checkpointer")
        return checkpointer
    except Exception as e:
        logger.warning(f"PostgresSaver unavailable: {e} — using MemorySaver")
        from langgraph.checkpoint.memory import MemorySaver
        return MemorySaver()

# ─── INTERRUPT NODE ──────────────────────────────────────────────────────────

async def human_input_node(state: SimulationState) -> dict:
    """
    Pauses graph execution here and waits for student response.
    The checkpointer saves full state at this point.
    When graph.invoke(Command(resume=student_response)) is called,
    execution continues from here with student_response in state.
    """
    student_response = interrupt("Waiting for student response")
    return {"student_response": student_response}

# ─── ROUTING ─────────────────────────────────────────────────────────────────

def route_after_career_fit(state: SimulationState) -> str:
    if state.get("should_loop_back"):
        return "scenario_node"
    elif state.get("is_final_scene"):
        return "report_node"
    else:
        return END

# ─── COMPILE GRAPH ───────────────────────────────────────────────────────────

def build_graph(checkpointer):
    builder = StateGraph(SimulationState)

    builder.add_node("supervisor_node", supervisor_node)
    builder.add_node("scenario_node", scenario_node)
    builder.add_node("human_input_node", human_input_node)
    builder.add_node("evaluation_node", evaluation_node)
    builder.add_node("career_fit_node", career_fit_node)
    builder.add_node("report_node", report_node)

    builder.add_edge(START, "supervisor_node")
    builder.add_edge("supervisor_node", "scenario_node")
    builder.add_edge("scenario_node", "human_input_node")   # pause after scene
    builder.add_edge("human_input_node", "evaluation_node") # resume with response
    builder.add_edge("evaluation_node", "career_fit_node")
    builder.add_conditional_edges(
        "career_fit_node",
        route_after_career_fit,
        {
            "scenario_node": "scenario_node",
            "report_node": "report_node",
            END: END,
        }
    )
    builder.add_edge("report_node", END)

    return builder.compile(checkpointer=checkpointer, interrupt_before=["human_input_node"])

checkpointer = _build_checkpointer()
graph = build_graph(checkpointer)

# ─── HELPERS ─────────────────────────────────────────────────────────────────

def _ctx_to_state(ctx: SceneGenerationContext) -> dict:
    """
    Convert SceneGenerationContext to initial SimulationState.
    Only used for FIRST scene (no prior state in checkpointer).
    For subsequent calls the checkpointer restores state automatically.
    """
    return {
        "simulation_session_id": ctx.simulation_session_id,
        "user_id": ctx.user_id,
        "domain": ctx.domain,
        "difficulty": ctx.difficulty,
        "scene_number": ctx.scene_number,
        "user_profile": {
            "self_rating": ctx.user_profile_snippet.self_rating,
            "core_interests": ctx.user_profile_snippet.core_interests,
        },
        "history": [
            {
                "scene": h.scene.model_dump(),
                "evaluation": h.evaluation.model_dump()
            }
            for h in (ctx.history or [])
        ],
        "active_domain": ctx.domain,
        "current_scene": None,
        "current_evaluation": None,
        "latest_score": 0.0,
        "should_loop_back": False,
        "lowered_difficulty": None,
        "fit_scores": None,
        "report": None,
        "is_final_scene": False,
        "loop_count": 0,        # only 0 on first scene — checkpointer carries it after
        "student_response": "",
    }

def _get_config(session_id: str) -> dict:
    """Thread config for checkpointer — ties all invocations to one session."""
    return {"configurable": {"thread_id": session_id}}

# ─── ENTRY POINTS ────────────────────────────────────────────────────────────

async def run_scenario_step(ctx: SceneGenerationContext) -> SceneContent:
    """
    Called by agent_client.generate_scene().
    First scene: initialise fresh state and run graph to interrupt.
    Subsequent scenes: resume from checkpointer state, 
    continuing after career_fit_node decided more scenes needed.
    """
    config = _get_config(ctx.simulation_session_id)

    # Check if there is existing checkpointed state for this session
    try:
        existing = await graph.aget_state(config)
        has_state = existing and existing.values
    except Exception:
        has_state = False

    if not has_state:
        # First scene — start fresh
        initial_state = _ctx_to_state(ctx)
        result = await graph.ainvoke(initial_state, config=config)
    else:
        # Subsequent scene — graph already paused after career_fit_node
        # Update scene_number in state then resume
        await graph.aupdate_state(
            config,
            {"scene_number": ctx.scene_number, "difficulty": ctx.difficulty}
        )
        result = await graph.ainvoke(None, config=config)

    scene_dict = result.get("current_scene", {})
    if not scene_dict:
        raise ValueError("scenario_node returned no scene")
    return SceneContent(**scene_dict)

async def run_evaluation_step(ctx: EvaluationContext) -> EvaluationResult:
    """
    Called by agent_client.evaluate_response().
    Resumes the graph from human_input_node with the student's response.
    The checkpointer provides loop_count, npc_states, history — no manual rebuild.
    """
    config = _get_config(ctx.simulation_session_id)
    student_response = ctx.user_response.raw_text or ""

    # Resume graph from interrupt with student response
    result = await graph.ainvoke(
        Command(resume=student_response),
        config=config
    )

    evaluation_dict = result.get("current_evaluation", {})
    if not evaluation_dict:
        raise ValueError("evaluation_node returned no evaluation")
    return EvaluationResult(**evaluation_dict)

async def run_fit_report_step(ctx: FitReportContext) -> FitReportResult:
    """
    Called by agent_client.generate_fit_report().
    Reads from checkpointed state or builds from ctx.
    """
    config = _get_config(ctx.sessions[0].simulation_session_id if ctx.sessions else "report")
    try:
        existing = await graph.aget_state(config)
        result = existing.values if existing else {}
    except Exception:
        result = {}

    report_dict = result.get("report")
    if report_dict:
        return FitReportResult(**report_dict)

    # Fallback: call report_node directly with ctx data
    from app.agents.nodes.report import generate_fit_report_from_ctx
    return await generate_fit_report_from_ctx(ctx)

async def run_mcq_generation_step(ctx: MCQGenerationContext) -> MCQGenerationResult:
    """
    Called by agent_client.generate_mcqs().
    Standalone — does not use the graph.
    """
    import json
    from app.agents.llm import get_llm, acall_llm_with_retry
    from langchain_core.messages import SystemMessage

    domain = ctx.chosen_field

    DOMAIN_MCQ_TOPICS = {
        "product_manager": {
            "focus": "sprint management, stakeholder communication, PRD writing, scope decisions, trade-off analysis",
            "examples": ["sprint at capacity + new feature request", "cutting tickets", "defining success metrics", "communicating decisions to different stakeholders", "MVP vs full scope"]
        },
        "sqa_engineer": {
            "focus": "bug severity, test case writing, regression testing, requirement gaps, cross-browser testing",
            "examples": ["classifying bug severity", "structured test cases", "developer pushback on severity", "finding spec gaps", "cross-environment priority"]
        },
        "data_analyst": {
            "focus": "metric anomaly investigation, correlation vs causation, data cleaning, root cause analysis",
            "examples": ["sudden metric drop", "tracking error vs real problem", "confounding variables", "data quality issues", "recommending action on incomplete data"]
        },
        "frontend_engineer": {
            "focus": "CSS debugging, responsive design, performance, accessibility, browser compatibility",
            "examples": ["layout issues across screen sizes", "CSS specificity", "page speed optimisation", "semantic HTML", "handling impossible client requests"]
        },
        "backend_engineer": {
            "focus": "API design, database optimisation, incident response, debugging slow endpoints",
            "examples": ["diagnosing slow API", "database indexing", "rollback vs hotfix", "REST API design", "database transactions"]
        }
    }

    FALLBACK = {
        "product_manager": [
            {"question": "Sprint is full. Sara requests a new feature urgently. First step?", "options": ["Add it immediately", "Ask about success metrics and check capacity first", "Reject without explanation", "Escalate to CEO"], "correct_option_index": 1},
            {"question": "Rayan says a feature needs 3 sprints. Sara says it must ship now. You:", "options": ["Side with Sara", "Side with Rayan", "Define minimum viable scope that satisfies the core goal", "Escalate to VP"], "correct_option_index": 2},
            {"question": "A good PRD must always include:", "options": ["Technical implementation details", "Success metrics, scope, and out-of-scope items", "Marketing copy", "Sprint ticket IDs"], "correct_option_index": 1},
            {"question": "Stakeholder says you committed to full scope but you only committed to exploring it. You:", "options": ["Agree — you must have miscommunicated", "Deny it", "Clarify what was actually said using facts, without blame", "Escalate to legal"], "correct_option_index": 2},
            {"question": "Why define out-of-scope explicitly in the PRD?", "options": ["To fill the template", "To prevent scope creep and manage expectations", "To give engineers fewer tasks", "Legal requirement"], "correct_option_index": 1}
        ],
        "sqa_engineer": [
            {"question": "Checkout bug affects only Safari mobile. Dan says not a blocker. You:", "options": ["Accept Dan's assessment", "Provide reproduction steps and argue severity based on revenue impact", "Close ticket", "Escalate without discussing"], "correct_option_index": 1},
            {"question": "A bug report must always include:", "options": ["Just a title", "Steps to reproduce, expected, actual, severity, environment", "Your opinion on priority", "Developer's name"], "correct_option_index": 1},
            {"question": "After a fix, copy-paste stops working in a previously working field. This is:", "options": ["A new feature request", "A regression bug", "Expected behavior", "Out of scope"], "correct_option_index": 1},
            {"question": "Spec says session expires after inactivity but never defines inactivity. This is:", "options": ["Fine — developer decides", "A requirement gap to flag before testing", "Intentional ambiguity", "Out of scope for QA"], "correct_option_index": 1},
            {"question": "Critical severity means:", "options": ["Minor UI issue", "Typo", "App crashes or core flow is completely blocked", "Feature enhancement"], "correct_option_index": 2}
        ],
        "data_analyst": [
            {"question": "Key metric drops 40% overnight. First step?", "options": ["Alert CEO immediately", "Check pipeline and tracking for errors before drawing conclusions", "Assume real business problem", "Wait a week"], "correct_option_index": 1},
            {"question": "Users who use feature X have higher retention. Most important question?", "options": ["How many use X?", "Is this correlation or causation?", "Who built X?", "Should we remove X?"], "correct_option_index": 1},
            {"question": "Dataset has 15% null values in a key column. You:", "options": ["Delete all null rows immediately", "Investigate why nulls exist before deciding", "Replace all with zero", "Ignore them"], "correct_option_index": 1},
            {"question": "New feature launched same week as major marketing campaign. Sales increased. You:", "options": ["Attribute to feature — timing matches", "Cannot isolate without controlled experiment", "Attribute to campaign only", "Run more SQL until one shows feature impact"], "correct_option_index": 1},
            {"question": "Effective data visualisation means:", "options": ["Use as many chart types as possible", "One clear insight per chart with appropriate type", "Show all available data regardless of relevance", "Make it look impressive"], "correct_option_index": 1}
        ],
        "frontend_engineer": [
            {"question": "Button renders 36px instead of 44px in Figma. First check?", "options": ["Report to designer", "CSS specificity conflicts, padding, box-sizing", "Hardcode height", "Ignore — close enough"], "correct_option_index": 1},
            {"question": "Client wants component that works on all screen sizes. First question?", "options": ["What screen sizes do users actually use based on analytics?", "Is mobile more important?", "Should we build a separate app?", "How many breakpoints?"], "correct_option_index": 0},
            {"question": "Page loads slowly on mobile. Most likely first thing to investigate?", "options": ["Server response time", "Unoptimised images, unused JS, render-blocking resources", "User's connection", "CSS animations"], "correct_option_index": 1},
            {"question": "Semantic HTML means:", "options": ["Use only div and span", "Use elements that describe meaning (nav, article, button) for accessibility and SEO", "Write HTML comments", "Use latest HTML5 regardless of support"], "correct_option_index": 1},
            {"question": "Client requests 5 new features on an already slow page. You:", "options": ["Add all 5 immediately", "Explain trade-off and ask which features deliver most value", "Refuse all 5", "Add them and fix performance later"], "correct_option_index": 1}
        ],
        "backend_engineer": [
            {"question": "API endpoint responds in 8s instead of 200ms. First step?", "options": ["Rewrite endpoint", "Add caching everywhere", "Profile to find bottleneck — DB query, external call, or computation", "Increase server resources"], "correct_option_index": 2},
            {"question": "DB query returns correct results but takes 30s on large table. Most likely fix?", "options": ["Rewrite in different language", "Add index on WHERE and JOIN columns", "Cache entire table", "Delete old records"], "correct_option_index": 1},
            {"question": "Designing an API multiple services will call. Most important?", "options": ["Make it fast at expense of clarity", "Consistent response shape, clear error codes, versioning, documentation", "Use newest tech stack", "Minimise endpoints"], "correct_option_index": 1},
            {"question": "Production deployment fails and users are impacted. First action?", "options": ["Fix bug in production immediately", "Rollback to last working version to restore service, then debug", "Tell users to clear cache", "Wait to see if it resolves"], "correct_option_index": 1},
            {"question": "Database transactions exist to:", "options": ["Speed up queries", "Ensure a group of operations all succeed or all fail — maintaining consistency", "Back up the database", "Allow multiple users to read simultaneously"], "correct_option_index": 1}
        ]
    }

    topic_config = DOMAIN_MCQ_TOPICS.get(domain, DOMAIN_MCQ_TOPICS["product_manager"])
    llm = get_llm(model="llama-3.1-8b-instant", temperature=0.3)

    prompt = f"""Generate exactly 5 multiple-choice questions testing practical {domain.replace('_', ' ')} workplace judgment.

FOCUS: {topic_config['focus']}
SCENARIO TYPES TO USE: {', '.join(topic_config['examples'])}

Rules:
- Every question must be a realistic workplace scenario
- Each question has exactly 4 options (A, B, C, D)
- Exactly one correct option
- Test real decision-making, not definitions

Return ONLY valid JSON, no markdown:
{{"questions": [{{"question": "...", "options": ["...", "...", "...", "..."], "correct_option_index": 0}}]}}"""

    try:
        response = await acall_llm_with_retry(llm, [SystemMessage(content=prompt)], stop=["```"])
        raw = response.content.strip().replace("```json","").replace("```","").strip()
        result = json.loads(raw)
        questions = result.get("questions", [])
        if len(questions) != 5:
            raise ValueError(f"Expected 5, got {len(questions)}")
        return MCQGenerationResult(questions=questions)
    except Exception as e:
        logger.error(f"MCQ generation failed: {e} — using fallback")
        fallback = FALLBACK.get(domain, FALLBACK["product_manager"])
        return MCQGenerationResult(questions=fallback)
