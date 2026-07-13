from app.schemas.agent_contracts import (
    Character,
    Domain,
    EvaluationContext,
    EvaluationResult,
    FitReportContext,
    FitReportResult,
    MCQGenerationContext,
    MCQGenerationResult,
    MCQQuestion,
    NpcStateUpdate,
    SceneContent,
    SceneGenerationContext,
    SceneMessage,
)

MOCK_TOTAL_SCENES = 3
MOCK_NPC_ID = "mock_npc_1"
ALL_DOMAINS: list[Domain] = [
    "product_manager",
    "sqa_engineer",
    "data_analyst",
    "frontend_engineer",
    "backend_engineer",
]


async def generate_scene(ctx: SceneGenerationContext) -> SceneContent:
    scene_number = ctx.scene_number
    return SceneContent(
        scene_number=scene_number,
        domain=ctx.domain,
        difficulty=ctx.difficulty,
        title=f"Mock Scene {scene_number} — {ctx.domain} ({ctx.difficulty})",
        narrative=(
            f"Deterministic mock scene {scene_number} of {MOCK_TOTAL_SCENES} "
            f"for domain '{ctx.domain}' at '{ctx.difficulty}' difficulty."
        ),
        context_data={"mock": True, "scene_number": scene_number},
        characters=[
            Character(id=MOCK_NPC_ID, name="Mock Stakeholder", role="product_owner", initial_trust=50)
        ],
        messages=[
            SceneMessage(
                sender=MOCK_NPC_ID,
                channel="chat",
                content=f"Here's the situation for scene {scene_number}.",
                time_offset_minutes=0,
            )
        ],
        response_format="free_text",
        prompt_for_response=f"How do you respond to the scene {scene_number} situation?",
        is_final_scene=scene_number >= MOCK_TOTAL_SCENES,
    )


async def evaluate_response(ctx: EvaluationContext) -> EvaluationResult:
    text = ctx.user_response.raw_text or ""
    overall_score = min(100.0, 40.0 + len(text) * 2)
    dimension_scores = {
        "analytical_reasoning": overall_score,
        "ambiguity_tolerance": overall_score,
        "communication_clarity": overall_score,
        "attention_to_detail": overall_score,
        "decisiveness": overall_score,
    }
    trust_score = min(100, 50 + int(overall_score / 10))

    return EvaluationResult(
        overall_score=overall_score,
        dimension_scores=dimension_scores,
        feedback_summary=f"Mock evaluation for scene {ctx.scene_number}: response length {len(text)} chars.",
        justification="Deterministic mock score based on response length.",
        npc_state_updates=[
            NpcStateUpdate(
                npc_id=MOCK_NPC_ID,
                trust_score=trust_score,
                sentiment="positive" if overall_score >= 60 else "neutral",
                memory_summary=f"Responded to scene {ctx.scene_number} with a {len(text)}-character response.",
            )
        ],
    )


async def generate_fit_report(ctx: FitReportContext) -> FitReportResult:
    all_scored = [e for session in ctx.sessions for e in session.evaluations]

    dimension_totals: dict[str, list[float]] = {}
    for scored in all_scored:
        for dim, value in scored.result.dimension_scores.items():
            dimension_totals.setdefault(dim, []).append(value)
    dimension_scores = {
        dim: round(sum(values) / len(values), 1) for dim, values in dimension_totals.items()
    }

    overall_avg = (
        round(sum(dimension_scores.values()) / len(dimension_scores), 1) if dimension_scores else 0.0
    )
    domain_fit_scores = {domain: overall_avg for domain in ALL_DOMAINS}
    ranked_domains = list(ALL_DOMAINS)  # deterministic mock: fixed order, all tied

    scored_dims = len(dimension_scores)
    if scored_dims >= 4:
        confidence_level = "high"
    elif scored_dims >= 2:
        confidence_level = "moderate"
    else:
        confidence_level = "directional"

    evidence_citations: dict[str, list[str]] = {dim: [] for dim in dimension_scores}
    for scored in all_scored:
        for dim, value in scored.result.dimension_scores.items():
            if dim in evidence_citations and value >= 65 and len(evidence_citations[dim]) < 3:
                evidence_citations[dim].append(scored.scene_evaluation_id)

    return FitReportResult(
        dimension_scores=dimension_scores,
        domain_fit_scores=domain_fit_scores,
        ranked_domains=ranked_domains,
        top_recommendation=ranked_domains[0],
        confidence_level=confidence_level,
        evidence_citations=evidence_citations,
        summary_narrative=(
            f"Mock fit report across {len(ctx.sessions)} session(s) and "
            f"{len(all_scored)} evaluated scene(s). Deterministic mock output, not real scoring."
        ),
        strengths=[f"Consistently scored well on {dim}" for dim, v in dimension_scores.items() if v >= 65][:3],
        growth_areas=[f"Room to improve on {dim}" for dim, v in dimension_scores.items() if v < 65][:2],
    )


async def generate_mcqs(ctx: MCQGenerationContext) -> MCQGenerationResult:
    questions = [
        MCQQuestion(
            question=f"Mock calibration question {i} for {ctx.chosen_field}.",
            options=["Option A", "Option B", "Option C", "Option D"],
            correct_option_index=i % 4,
        )
        for i in range(1, 6)
    ]
    return MCQGenerationResult(questions=questions)
