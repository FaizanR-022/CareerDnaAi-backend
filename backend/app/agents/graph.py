import logging
import os

logger = logging.getLogger(__name__)

from langgraph.graph import StateGraph, START, END
from app.agents.state import SimulationState
from app.agents.nodes.scenario import scenario_node
from app.agents.nodes.evaluation import evaluation_node
from app.agents.nodes.career_fit import career_fit_node
from app.schemas.agent_contracts import (
    EvaluationContext, EvaluationResult,
    FitReportContext, FitReportResult,
    MCQGenerationContext, MCQGenerationResult,
    SceneContent, SceneGenerationContext,
)

from app.agents.nodes.supervisor import supervisor_node
from app.agents.nodes.report import report_node

def route_after_career_fit(state: SimulationState):
    if state.get("should_loop_back"):
        return "scenario_node"
    elif state.get("is_final_scene"):
        return "report_node"
    else:
        return END

# TWO SEPARATE GRAPHS:
# 1. scene_graph — invoked by generate_scene()
# 2. eval_graph  — invoked by evaluate_response()
# This is because LangGraph needs a clean entry point per call type.

# Scene generation graph
scene_builder = StateGraph(SimulationState)
scene_builder.add_node("supervisor_node", supervisor_node)
scene_builder.add_node("scenario_node", scenario_node)
scene_builder.add_edge(START, "supervisor_node")
scene_builder.add_edge("supervisor_node", "scenario_node")
scene_builder.add_edge("scenario_node", END)

# Evaluation graph (includes feedback loop)
eval_builder = StateGraph(SimulationState)
eval_builder.add_node("evaluation_node", evaluation_node)
eval_builder.add_node("career_fit_node", career_fit_node)
eval_builder.add_node("scenario_node", scenario_node)
eval_builder.add_node("report_node", report_node)
eval_builder.add_edge(START, "evaluation_node")
eval_builder.add_edge("evaluation_node", "career_fit_node")
eval_builder.add_conditional_edges(
    "career_fit_node",
    route_after_career_fit,
    {
        "scenario_node": "scenario_node",
        "report_node": "report_node",
        END: END,
    }
)
eval_builder.add_edge("scenario_node", END)
eval_builder.add_edge("report_node", END)


# ─── CHECKPOINTER SETUP ────────────────────────────────────────────────────────
# Primary: PostgresSaver using SUPABASE_CONN_STRING connection string.
# Fallback: MemorySaver when the env var or DB is unavailable (dev / CI).

def _build_graphs_with_postgres(conn_str: str):
    """Compile both graphs using a PostgresSaver connection pool."""
    # Lazy import — package is optional (langgraph-checkpoint-postgres)
    from langgraph.checkpoint.postgres import PostgresSaver  # noqa: PLC0415
    with PostgresSaver.from_conn_string(conn_str) as saver:
        # Run DB migrations for internal checkpointer tables automatically
        saver.setup()
        sg = scene_builder.compile(checkpointer=saver)
        eg = eval_builder.compile(checkpointer=saver)
    return sg, eg


def _build_graphs_with_memory():
    """Fallback: compile both graphs using in-process MemorySaver."""
    from langgraph.checkpoint.memory import MemorySaver
    saver = MemorySaver()
    sg = scene_builder.compile(checkpointer=saver)
    eg = eval_builder.compile(checkpointer=saver)
    return sg, eg


supabase_conn_str: str | None = os.environ.get("SUPABASE_CONN_STRING")

try:
    if not supabase_conn_str:
        raise ValueError("SUPABASE_CONN_STRING environment variable is not set.")
    scene_graph, eval_graph = _build_graphs_with_postgres(supabase_conn_str)
    logger.info("PostgresSaver checkpointer initialised successfully.")
except Exception as e:
    logger.warning(
        f"PostgresSaver unavailable ({e}) — falling back to MemorySaver. "
        "Set SUPABASE_CONN_STRING in .env for persistent checkpointing."
    )
    scene_graph, eval_graph = _build_graphs_with_memory()



# --- Entry points called by agent_client.py ---

def run_scenario_step(ctx: SceneGenerationContext) -> SceneContent:
    """Convert SceneGenerationContext to SimulationState and run scene graph."""
    state = {
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
            {"scene": h.scene.model_dump(), "evaluation": h.evaluation.model_dump()}
            for h in (ctx.history or [])
        ],
        # Defaults
        "active_domain": ctx.domain,
        "current_scene": None,
        "current_evaluation": None,
        "latest_score": 0.0,
        "should_loop_back": False,
        "lowered_difficulty": None,
        "fit_scores": None,
        "report": None,
        "is_final_scene": False,
        "loop_count": 0,
        "student_response": "",
    }
    config = {"configurable": {"thread_id": ctx.simulation_session_id}}
    result = scene_graph.invoke(state, config=config)
    scene_dict = result.get("current_scene", {})
    # Convert dict to SceneContent
    return SceneContent(**scene_dict)

def run_evaluation_step(ctx: EvaluationContext) -> EvaluationResult:
    """Convert EvaluationContext to SimulationState and run eval graph."""
    state = {
        "simulation_session_id": ctx.simulation_session_id,
        "user_id": ctx.user_id,
        "domain": ctx.domain,
        "difficulty": ctx.difficulty,
        "scene_number": ctx.scene_number,
        "user_profile": {},
        "history": [
            {"scene": h.scene.model_dump(), "evaluation": h.evaluation.model_dump()}
            for h in (ctx.history or [])
        ],
        "current_scene": ctx.scene_content.model_dump(),
        "student_response": ctx.user_response.raw_text or "",
        # Defaults
        "active_domain": ctx.domain,
        "current_evaluation": None,
        "latest_score": 0.0,
        "should_loop_back": False,
        "lowered_difficulty": None,
        "fit_scores": None,
        "report": None,
        "is_final_scene": ctx.scene_content.is_final_scene,
        "loop_count": 0,
    }
    config = {"configurable": {"thread_id": ctx.simulation_session_id}}
    result = eval_graph.invoke(state, config=config)
    evaluation_dict = result.get("current_evaluation", {})
    if "extra" not in evaluation_dict:
        evaluation_dict["extra"] = {}
    if result.get("lowered_difficulty"):
        evaluation_dict["extra"]["lowered_difficulty"] = result["lowered_difficulty"]
    return EvaluationResult(**evaluation_dict)

def run_fit_report_step(ctx: FitReportContext) -> FitReportResult:
    """
    Constructs the FitReportResult by aggregating student history, calculating fit vectors,
    and invoking the LLM qualitative evaluator.
    """
    from app.agents.career_fit_agent import generate_fit_report_data
    from app.agents.nodes.report import report_node

    # Convert summaries list back to sessions database shapes for generate_fit_report_data
    sessions_payload = []
    history_entries = []
    for session in ctx.sessions:
        decisions_log = []
        for scored in session.evaluations:
            res = scored.result
            decisions_log.append({
                "id": scored.scene_evaluation_id,
                "dimension_scores": res.dimension_scores,
            })
            # Also keep a flat state history structure to feed the report LLM node
            history_entries.append({
                "scene": {
                    "scene_number": scored.scene_number,
                    "title": f"Scene {scored.scene_number}",
                },
                "evaluation": {
                    "scene_evaluation_id": scored.scene_evaluation_id,
                    "overall_score": res.overall_score,
                    "dimension_scores": res.dimension_scores,
                    "feedback_summary": res.feedback_summary,
                    "npc_state_updates": res.npc_state_updates,
                }
            })

        sessions_payload.append({
            "domain": session.domain,
            "scores": {
                # Map averages from session evaluation logs
                dim: sum(e.result.dimension_scores.get(dim, 50.0) for e in session.evaluations) / max(len(session.evaluations), 1)
                for dim in ["analytical_reasoning", "ambiguity_tolerance", "communication_clarity", "attention_to_detail", "decisiveness"]
            },
            "decisions_log": decisions_log
        })

    # Get fit result using the deterministic aggregation engine
    fit_data = generate_fit_report_data(ctx.user_id, sessions_payload)

    # Invoke report LLM node to get the qualitative narration block
    state_mock = {"history": history_entries}
    llm_report = report_node(state_mock).get("report", {})

    return FitReportResult(
        domain_fit_scores=fit_data["domain_fit_scores"],
        ranked_domains=fit_data["ranked_domains"],
        top_recommendation=fit_data["top_domain"],
        confidence_level=fit_data["confidence_level"],
        evidence_citations=fit_data["evidence_citations"],
        summary_narrative=llm_report.get("summary_narrative", "Baseline capabilites match requirements."),
        strengths=llm_report.get("strengths", []),
        growth_areas=llm_report.get("growth_areas", []),
    )


def run_mcq_generation_step(ctx: MCQGenerationContext) -> MCQGenerationResult:
    import json
    import logging
    from app.agents.llm import get_llm
    from langchain_core.messages import SystemMessage
    logger = logging.getLogger(__name__)

    domain = ctx.chosen_field

    FALLBACK_QUESTIONS = {
        "product_manager": [
            {
                "question": "Your sprint board is full and Sara from Marketing urgently requests a new feature. What is your FIRST step?",
                "options": [
                    "Add it immediately to keep Sara happy",
                    "Ask Sara what success looks like and check sprint capacity first",
                    "Reject the request without explanation",
                    "Escalate directly to the CEO"
                ],
                "correct_option_index": 1
            },
            {
                "question": "Rayan (Engineering Lead) says a feature will take 3 sprints. Sara says it must ship this sprint. What do you do?",
                "options": [
                    "Side with Sara — she is the business stakeholder",
                    "Side with Rayan — never overrule engineering estimates",
                    "Mediate: define the minimum viable scope that satisfies the core business goal",
                    "Escalate to the VP immediately without making a decision"
                ],
                "correct_option_index": 2
            },
            {
                "question": "What fields must a complete PRD always include?",
                "options": [
                    "Technical implementation details and code snippets",
                    "Success metrics, scope, out-of-scope items, and stakeholders",
                    "Marketing copy and pricing strategy",
                    "Sprint ticket IDs and story points"
                ],
                "correct_option_index": 1
            },
            {
                "question": "A stakeholder says you committed to a full feature scope but you only committed to exploring it. What is the best response?",
                "options": [
                    "Agree with them — you must have miscommunicated",
                    "Deny it happened and move on",
                    "Clarify what was actually said without blaming them, using facts",
                    "Escalate to legal immediately"
                ],
                "correct_option_index": 2
            },
            {
                "question": "Why should a PM define 'out of scope' explicitly in the PRD?",
                "options": [
                    "To fill out the document template",
                    "To prevent scope creep and manage stakeholder expectations clearly",
                    "To give engineers fewer tasks",
                    "Legal requirement for product documentation"
                ],
                "correct_option_index": 1
            }
        ],
        "sqa_engineer": [
            {
                "question": "You find a checkout bug that affects only Safari mobile users. Dan says it is not a blocker. What do you do?",
                "options": [
                    "Accept Dan's assessment — he built it",
                    "Provide reproduction steps and argue severity based on user impact and revenue risk",
                    "Close the ticket — too few users affected",
                    "Immediately escalate to the PM without discussing with Dan"
                ],
                "correct_option_index": 1
            },
            {
                "question": "What must a bug report always include?",
                "options": [
                    "Just a descriptive title",
                    "Steps to reproduce, expected behavior, actual behavior, severity, and environment",
                    "Your personal opinion on whether it should be fixed",
                    "The name of the developer responsible"
                ],
                "correct_option_index": 1
            },
            {
                "question": "After a developer fixes a bug, you find copy-paste no longer works in a field that previously worked. This is:",
                "options": [
                    "A new feature request",
                    "A regression bug introduced by the fix",
                    "Expected behavior after a patch",
                    "Out of scope for this test cycle"
                ],
                "correct_option_index": 1
            },
            {
                "question": "The spec says 'session expires after inactivity' but never defines what inactivity means. This is:",
                "options": [
                    "Acceptable — the developer decides implementation details",
                    "A requirement gap that must be flagged to the PM before testing",
                    "An intentional feature — ambiguity gives flexibility",
                    "Out of scope for QA to question"
                ],
                "correct_option_index": 1
            },
            {
                "question": "Critical severity in bug triage means:",
                "options": [
                    "A minor UI alignment issue",
                    "A typo visible to users",
                    "The application crashes or a core user flow is completely blocked",
                    "A feature enhancement request"
                ],
                "correct_option_index": 2
            }
        ],
        "data_analyst": [
            {
                "question": "A key metric drops 40% overnight. What is your first step?",
                "options": [
                    "Immediately alert the CEO",
                    "Check if the data pipeline or tracking code has an error before drawing conclusions",
                    "Assume it is a real business problem and start analysis",
                    "Wait a week to see if it recovers"
                ],
                "correct_option_index": 1
            },
            {
                "question": "A stakeholder says 'users who use feature X have higher retention'. What is the most important question to ask?",
                "options": [
                    "How many users use feature X?",
                    "Is this correlation or causation — do highly engaged users just happen to use X?",
                    "Which engineer built feature X?",
                    "Should we remove X to test the impact?"
                ],
                "correct_option_index": 1
            },
            {
                "question": "You notice a dataset has 15% null values in a key column. What do you do?",
                "options": [
                    "Delete all rows with null values immediately",
                    "Investigate why nulls exist before deciding how to handle them",
                    "Replace all nulls with zero",
                    "Ignore them — 85% of data is still valid"
                ],
                "correct_option_index": 1
            },
            {
                "question": "What makes a data visualization effective?",
                "options": [
                    "Using as many colors and chart types as possible",
                    "Showing one clear insight per chart with appropriate chart type for the data",
                    "Including all available data points regardless of relevance",
                    "Making it look impressive for presentations"
                ],
                "correct_option_index": 1
            },
            {
                "question": "A VP asks you to prove that a new feature caused the sales increase. The feature launched the same week as a major marketing campaign. What do you say?",
                "options": [
                    "Confirm the feature caused it — the timing matches",
                    "We cannot isolate the feature's impact without a controlled experiment; both launched simultaneously",
                    "The marketing campaign caused it, not the feature",
                    "Run more SQL queries until one shows the feature impact"
                ],
                "correct_option_index": 1
            }
        ],
        "frontend_engineer": [
            {
                "question": "A designer's Figma mockup shows a button at 44px height but the browser renders it at 36px. What do you check first?",
                "options": [
                    "Report a bug to the designer",
                    "Check CSS specificity conflicts, padding, and box-sizing settings",
                    "Hardcode the height in pixels",
                    "Ignore it — close enough"
                ],
                "correct_option_index": 1
            },
            {
                "question": "A client wants a component that 'works on all screen sizes'. What is your first clarifying question?",
                "options": [
                    "What screen sizes do your users actually use based on analytics?",
                    "Is mobile more important than desktop?",
                    "Should we build a separate mobile app?",
                    "How many breakpoints do you want?"
                ],
                "correct_option_index": 0
            },
            {
                "question": "A page loads slowly on mobile. What is the most likely first thing to investigate?",
                "options": [
                    "Server response time",
                    "Unoptimized images, unused JavaScript, and render-blocking resources",
                    "The user's internet connection",
                    "CSS animations"
                ],
                "correct_option_index": 1
            },
            {
                "question": "What does 'semantic HTML' mean and why does it matter?",
                "options": [
                    "Using only div and span elements for cleaner code",
                    "Using HTML elements that describe their meaning (nav, article, button) for accessibility and SEO",
                    "Writing HTML comments to explain the code",
                    "Using the latest HTML5 features regardless of browser support"
                ],
                "correct_option_index": 1
            },
            {
                "question": "A client asks you to add 5 new features to a landing page that is already loading slowly. What do you say?",
                "options": [
                    "Add all 5 immediately to keep the client happy",
                    "Explain the performance trade-off and ask which features deliver the most value to prioritize",
                    "Refuse all 5 — performance is non-negotiable",
                    "Add them and fix performance later"
                ],
                "correct_option_index": 1
            }
        ],
        "backend_engineer": [
            {
                "question": "An API endpoint is responding in 8 seconds instead of the expected 200ms. What is your first step?",
                "options": [
                    "Rewrite the entire endpoint",
                    "Add caching everywhere immediately",
                    "Profile the request to find the bottleneck — database query, external API call, or computation",
                    "Increase the server resources"
                ],
                "correct_option_index": 2
            },
            {
                "question": "A database query returns correct results but takes 30 seconds on a large table. What is the most likely fix?",
                "options": [
                    "Rewrite the query in a different language",
                    "Add an index on the columns used in WHERE and JOIN clauses",
                    "Cache the entire table in memory",
                    "Reduce the table size by deleting old records"
                ],
                "correct_option_index": 1
            },
            {
                "question": "You are designing an API endpoint that multiple services will call. What is most important?",
                "options": [
                    "Making it as fast as possible at the expense of clarity",
                    "Consistent response shape, clear error codes, versioning, and documentation",
                    "Using the newest technology stack available",
                    "Minimizing the number of endpoints"
                ],
                "correct_option_index": 1
            },
            {
                "question": "A production deployment fails and users are impacted. What do you do first?",
                "options": [
                    "Fix the bug immediately in production",
                    "Rollback to the last working version to restore service, then debug",
                    "Tell users to clear their cache",
                    "Wait to see if it resolves itself"
                ],
                "correct_option_index": 1
            },
            {
                "question": "What is the purpose of database transactions?",
                "options": [
                    "To speed up database queries",
                    "To ensure a group of operations either all succeed or all fail — maintaining data consistency",
                    "To back up the database",
                    "To allow multiple users to read simultaneously"
                ],
                "correct_option_index": 1
            }
        ]
    }

    DOMAIN_MCQ_TOPICS = {
        "product_manager": {
            "focus": "sprint management, stakeholder communication, PRD writing, scope decisions, trade-off analysis",
            "context": "You are testing whether a CS student understands real Product Manager responsibilities at a tech startup",
            "example_topics": [
                "How to respond when sprint is full and stakeholder requests new feature",
                "Deciding which ticket to cut when capacity is over",
                "Defining success metrics before committing to scope",
                "Communicating decisions to engineering vs marketing stakeholders",
                "MVP vs full feature scope decisions"
            ]
        },
        "sqa_engineer": {
            "focus": "bug severity classification, test case writing, regression testing, requirement gap analysis, cross-browser testing",
            "context": "You are testing whether a CS student understands real Software QA Engineer responsibilities",
            "example_topics": [
                "Classifying bug severity (critical vs major vs minor)",
                "Writing structured test cases with steps, expected, actual results",
                "Handling developer pushback on bug severity",
                "Finding requirement gaps before testing starts",
                "Cross-environment testing prioritisation"
            ]
        },
        "data_analyst": {
            "focus": "metric anomaly investigation, correlation vs causation, data cleaning, root cause analysis, presenting insights",
            "context": "You are testing whether a CS student understands real Data Analyst responsibilities",
            "example_topics": [
                "First step when a key metric drops unexpectedly",
                "Distinguishing tracking errors from real business problems",
                "Handling confounding variables in analysis",
                "Communicating uncertainty in data findings",
                "Recommending action based on incomplete data"
            ]
        },
        "frontend_engineer": {
            "focus": "CSS debugging, responsive design, performance optimisation, accessibility, browser compatibility",
            "context": "You are testing whether a CS student understands real Frontend Engineer responsibilities",
            "example_topics": [
                "Diagnosing layout issues across screen sizes",
                "CSS specificity and inheritance conflicts",
                "Image and asset optimisation for page speed",
                "Semantic HTML and accessibility",
                "Handling impossible client requests professionally"
            ]
        },
        "backend_engineer": {
            "focus": "API design, database query optimisation, incident response, debugging slow endpoints, system architecture",
            "context": "You are testing whether a CS student understands real Backend Engineer responsibilities",
            "example_topics": [
                "Diagnosing a slow API endpoint",
                "Database indexing decisions",
                "Rollback vs hotfix in a production incident",
                "REST API design principles",
                "Database transaction and consistency"
            ]
        }
    }

    llm = get_llm(model="llama-3.1-8b-instant", temperature=0.3)

    domain_config = DOMAIN_MCQ_TOPICS.get(domain, DOMAIN_MCQ_TOPICS["product_manager"])
    
    prompt = f"""Generate exactly 5 multiple-choice questions to assess a CS student's practical knowledge for a {domain.replace('_', ' ')} role at a tech startup.

CONTEXT: {domain_config['context']}

FOCUS AREAS (questions must come from these topics):
{chr(10).join(f'- {t}' for t in domain_config['example_topics'])}

RULES:
- Every question must be a realistic workplace scenario, not a definition or theory question
- Wrong: "What does MOSCOW stand for?" (definition)  
- Right: "Sprint is full, stakeholder requests new feature. What do you do first?" (scenario)
- Each question has exactly 4 options (A, B, C, D)
- Exactly one correct option per question
- Questions must have clear correct answers that a competent professional would know
- Difficulty: medium — not too easy, not trick questions

Return ONLY valid JSON, no markdown, no backticks:
{{
  "questions": [
    {{
      "question": "realistic workplace scenario question",
      "options": ["option A", "option B", "option C", "option D"],
      "correct_option_index": <0, 1, 2, or 3>
    }}
  ]
}}"""

    try:
        response = llm.invoke(
            [SystemMessage(content=prompt)],
            stop=["```"]
        )
        raw = response.content.strip().replace("```json","").replace("```","").strip()
        result = json.loads(raw)
        questions = result.get("questions", [])
        if len(questions) != 5:
            raise ValueError(f"Expected 5 questions, got {{len(questions)}}")
        logger.info(f"MCQ generation succeeded for domain: {{domain}}")
        return MCQGenerationResult(questions=questions)
    except Exception as e:
        logger.error(f"MCQ generation failed: {{e}} — using fallback")
        fallback = FALLBACK_QUESTIONS.get(domain, FALLBACK_QUESTIONS["product_manager"])
        return MCQGenerationResult(questions=fallback)
