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

async def run_scenario_step(ctx: SceneGenerationContext) -> SceneContent:
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
    result = await scene_graph.ainvoke(state, config=config)
    scene_dict = result.get("current_scene", {})
    # Convert dict to SceneContent
    return SceneContent(**scene_dict)

async def run_evaluation_step(ctx: EvaluationContext) -> EvaluationResult:
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
    result = await eval_graph.ainvoke(state, config=config)
    evaluation_dict = result.get("current_evaluation", {})
    if "extra" not in evaluation_dict:
        evaluation_dict["extra"] = {}
    if result.get("lowered_difficulty"):
        evaluation_dict["extra"]["lowered_difficulty"] = result["lowered_difficulty"]
    return EvaluationResult(**evaluation_dict)

async def run_fit_report_step(ctx: FitReportContext) -> FitReportResult:
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
    report_result = await report_node(state_mock)
    llm_report = report_result.get("report", {})

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


async def run_mcq_generation_step(ctx: MCQGenerationContext) -> MCQGenerationResult:
    import json
    import logging
    from app.agents.llm import get_llm
    from langchain_core.messages import SystemMessage
    logger = logging.getLogger(__name__)

    domain = ctx.chosen_field

    FALLBACK_QUESTIONS = {
        "product_manager": [
            {
                "question": "A stakeholder demands a new feature mid-sprint. The sprint is already over capacity. What is the most appropriate PM response?",
                "options": [
                    "Say yes and tell engineers they need to work over the weekend",
                    "Say no immediately without discussing it",
                    "Acknowledge the request, show the current sprint commitments, and ask what should be deprioritized to fit it in",
                    "Quietly add it to the backlog and ignore the stakeholder"
                ],
                "correct_option_index": 2
            },
            {
                "question": "Engineering team says a feature will take 4 weeks. Sales promised it to a client in 2 weeks. What do you do?",
                "options": [
                    "Tell engineering to finish it in 2 weeks no matter what",
                    "Work with engineering to descope non-essential requirements to build an MVP in 2 weeks",
                    "Tell sales it's impossible and refuse to help",
                    "Add more engineers to the project to double the speed"
                ],
                "correct_option_index": 1
            },
            {
                "question": "You are writing a PRD (Product Requirements Document). What is the most important section to include?",
                "options": [
                    "The exact code architecture the engineers should use",
                    "The exact CSS hex codes for the UI",
                    "The core user problem, success metrics, and acceptance criteria",
                    "A list of all competitors in the market"
                ],
                "correct_option_index": 2
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
                "question": "A developer asks you to test their feature but provides no PRD or requirements. What is your first step?",
                "options": [
                    "Start testing randomly and hope you find bugs",
                    "Refuse to test it until a full 50-page document is written",
                    "Ask the developer for a quick overview of expected behavior and edge cases before starting",
                    "Write the code for them"
                ],
                "correct_option_index": 2
            },
            {
                "question": "You find a critical bug in production right after a release. What is the priority?",
                "options": [
                    "Find out which developer caused it and blame them",
                    "Write a 10-page post-mortem document",
                    "Provide clear reproduction steps and logs so the team can hotfix or rollback immediately",
                    "Wait until tomorrow to report it"
                ],
                "correct_option_index": 2
            },
            {
                "question": "What is the primary purpose of regression testing?",
                "options": [
                    "To find completely new features to build",
                    "To ensure that recent code changes haven't broken previously working functionality",
                    "To test the speed of the application",
                    "To check if the UI looks pretty"
                ],
                "correct_option_index": 1
            },
            {
                "question": "A bug is intermittent (only happens 10% of the time). How do you log it?",
                "options": [
                    "Ignore it because it's too hard to reproduce",
                    "Log it with exact environment details, frequency (1/10), and all console logs available",
                    "Tell the developer it's completely broken",
                    "Wait until it happens 100% of the time before logging"
                ],
                "correct_option_index": 1
            }
        ],
        "data_analyst": [
            {
                "question": "The VP of Analytics says signups dropped 20% yesterday. What is your first action?",
                "options": [
                    "Tell marketing their campaign failed",
                    "Check if the tracking pixel or data pipeline broke before assuming user behavior changed",
                    "Change the dashboard to hide the drop",
                    "Run a machine learning model to predict tomorrow's signups"
                ],
                "correct_option_index": 1
            },
            {
                "question": "You find a strong correlation between users who change their profile picture and users who buy subscriptions. What should you tell the PM?",
                "options": [
                    "We must force everyone to change their profile picture to increase revenue",
                    "Correlation does not imply causation; we should run an A/B test to see if prompting a picture change drives revenue",
                    "The data is probably wrong",
                    "Profile pictures are the only thing that matters in the app"
                ],
                "correct_option_index": 1
            },
            {
                "question": "A dataset contains 5% missing values in a critical revenue column. How do you handle it for a high-stakes financial report?",
                "options": [
                    "Fill them all with zeroes",
                    "Delete the rows entirely without telling anyone",
                    "Investigate why they are missing, document the gap, and exclude/impute carefully while noting the assumption in the report",
                    "Make up random numbers to fill the gaps"
                ],
                "correct_option_index": 2
            },
            {
                "question": "You need to explain a complex statistical model to a non-technical stakeholder. How do you approach it?",
                "options": [
                    "Use as much math jargon as possible to sound smart",
                    "Focus on the business impact, actionable insights, and confidence level rather than the math",
                    "Give them the raw Python code to read",
                    "Refuse to explain it because they wouldn't understand"
                ],
                "correct_option_index": 1
            },
            {
                "question": "What is the risk of presenting data without confidence intervals or error margins?",
                "options": [
                    "It makes the dashboard load slower",
                    "Stakeholders might make rigid decisions based on noisy data, believing it to be absolute truth",
                    "It takes too much time to calculate",
                    "There is no risk; data is always perfect"
                ],
                "correct_option_index": 1
            }
        ],
        "frontend_engineer": [
            {
                "question": "A client demands a 3D animation that causes the page to lag heavily on mobile. What do you do?",
                "options": [
                    "Implement it exactly as requested — it's their problem",
                    "Refuse to do it and tell them they have bad taste",
                    "Explain the performance impact and propose a lighter CSS alternative that achieves a similar feel",
                    "Tell them mobile users don't matter"
                ],
                "correct_option_index": 2
            },
            {
                "question": "You are reviewing a PR that uses highly specific CSS selectors (e.g., `div#main .container ul li.active`). Why is this bad?",
                "options": [
                    "It makes the CSS file smaller",
                    "It causes specificity wars, making styles incredibly hard to override later",
                    "Browsers cannot read specific selectors",
                    "It is actually the best practice"
                ],
                "correct_option_index": 1
            },
            {
                "question": "A visually impaired user cannot navigate a custom dropdown menu you built. What did you likely forget?",
                "options": [
                    "Adding more CSS colors",
                    "Proper ARIA roles and keyboard (tab) navigation support",
                    "Using a JavaScript framework like React",
                    "Making the font bigger"
                ],
                "correct_option_index": 1
            },
            {
                "question": "Your Lighthouse performance score is 30/100 due to 'Largest Contentful Paint' (LCP). What is a common fix?",
                "options": [
                    "Add more JavaScript",
                    "Optimize and compress the hero image, and ensure it loads early without render-blocking JS",
                    "Delete all the CSS",
                    "Tell the PM Lighthouse doesn't matter"
                ],
                "correct_option_index": 1
            },
            {
                "question": "The design team hands off a UI that requires 5 different custom font families. What is your concern?",
                "options": [
                    "It will look too beautiful",
                    "Loading 5 web fonts will severely degrade page load speed and cause FOIT (Flash of Invisible Text)",
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
        response = await llm.ainvoke(
            [SystemMessage(content=prompt)],
            stop=["```"]
        )
        raw = response.content.strip().replace("```json","").replace("```","").strip()
        result = json.loads(raw)
        questions = result.get("questions", [])
        if len(questions) != 5:
            raise ValueError(f"Expected 5 questions, got {len(questions)}")
        logger.info(f"MCQ generation succeeded for domain: {domain}")
        return MCQGenerationResult(questions=questions)
    except Exception as e:
        logger.error(f"MCQ generation failed: {{e}} — using fallback")
        fallback = FALLBACK_QUESTIONS.get(domain, FALLBACK_QUESTIONS["product_manager"])
        return MCQGenerationResult(questions=fallback)
