from typing import Literal

from pydantic import BaseModel, Field

Domain = Literal[
    "product_manager", "sqa_engineer", "data_analyst", "frontend_engineer", "backend_engineer"
]
Difficulty = Literal["easy", "medium", "hard"]
Sentiment = Literal["positive", "neutral", "negative"]
ResponseFormat = Literal["free_text", "structured", "code"]


class Character(BaseModel):
    id: str
    name: str
    role: str
    initial_trust: int = Field(50, ge=0, le=100)


class SceneMessage(BaseModel):
    sender: str
    channel: str
    content: str
    time_offset_minutes: int = 0


class SceneContent(BaseModel):
    """Agent layer's output for one scene. `context_data` and `extra` are
    opaque to backend — stored as JSONB in full, never destructured."""

    scene_number: int
    domain: Domain
    difficulty: Difficulty
    title: str
    narrative: str
    context_data: dict = Field(default_factory=dict)
    characters: list[Character] = Field(default_factory=list)
    messages: list[SceneMessage] = Field(default_factory=list)
    response_format: ResponseFormat = "free_text"
    response_choices: list[str] | None = None
    prompt_for_response: str
    hint: str | None = None
    is_final_scene: bool = False
    extra: dict = Field(default_factory=dict)


class NpcStateUpdate(BaseModel):
    npc_id: str
    trust_score: int = Field(..., ge=0, le=100)
    sentiment: Sentiment
    memory_summary: str | None = None


class EvaluationResult(BaseModel):
    """Agent layer's output for one evaluated response. `dimension_scores`
    is free-form — backend never hardcodes dimension names, since scoring
    semantics are entirely the agent layer's business."""

    overall_score: float = Field(..., ge=0, le=100)
    dimension_scores: dict[str, float] = Field(default_factory=dict)
    feedback_summary: str
    behavioral_flags: list[str] = Field(default_factory=list)
    justification: str | None = None
    reasoning: str | None = None
    npc_state_updates: list[NpcStateUpdate] = Field(default_factory=list)
    extra: dict = Field(default_factory=dict)


class HistoryEntry(BaseModel):
    """One prior scene + its evaluation, in generation order. Used to give
    the agent layer full context for generating the next scene or scoring
    the current response."""

    scene: SceneContent
    evaluation: EvaluationResult
    student_response: str | None = None


class UserProfileSnippet(BaseModel):
    self_rating: int | None = Field(None, ge=1, le=5)
    core_interests: list[str] = Field(default_factory=list)


class SceneGenerationContext(BaseModel):
    """Input to the agent layer's "generate a scene" entry point."""

    simulation_session_id: str
    user_id: str
    domain: Domain
    difficulty: Difficulty
    scene_number: int
    user_profile_snippet: UserProfileSnippet
    history: list[HistoryEntry] = Field(default_factory=list)


class SubmittedResponse(BaseModel):
    raw_text: str | None = None
    structured: dict | None = None
    response_time_seconds: int | None = None
    revision_count: int = 0


class EvaluationContext(BaseModel):
    """Input to the agent layer's "evaluate a response" entry point."""

    simulation_session_id: str
    user_id: str
    domain: Domain
    difficulty: Difficulty
    scene_number: int
    scene_content: SceneContent
    user_response: SubmittedResponse
    history: list[HistoryEntry] = Field(default_factory=list)


class ScoredEvaluation(BaseModel):
    """One evaluated scene, paired with its real persisted DB id so the
    agent layer can cite specific evaluations back as evidence."""

    scene_evaluation_id: str
    scene_number: int
    result: EvaluationResult


class SessionEvaluationSummary(BaseModel):
    simulation_session_id: str
    domain: Domain
    difficulty: Difficulty
    evaluations: list[ScoredEvaluation] = Field(default_factory=list)


class FitReportContext(BaseModel):
    """Input to the agent layer's "generate a fit report" entry point."""

    user_id: str
    sessions: list[SessionEvaluationSummary]


class QuestionScore(BaseModel):
    """One answer from the client's dynamic onboarding self-assessment form
    (questions are generated client-side, not static)."""

    question: str
    score: int = Field(..., ge=1, le=5)


class MCQQuestion(BaseModel):
    question: str
    options: list[str]
    correct_option_index: int = Field(..., ge=0)


class MCQGenerationContext(BaseModel):
    """Input to the agent layer's "generate calibration MCQs" entry point.
    Nothing here is persisted — used once to generate the questions, then
    discarded; the client scores the answers and assigns difficulty itself."""

    user_id: str
    chosen_field: Domain
    self_assessment: list[QuestionScore] = Field(default_factory=list)


class MCQGenerationResult(BaseModel):
    """Five domain-knowledge MCQs (with answers) for client-side difficulty
    calibration."""

    questions: list[MCQQuestion] = Field(default_factory=list)


class FitReportResult(BaseModel):
    """Agent layer's output for a fit report — transient, not what gets
    persisted directly (backend flattens this into the career_dna_reports
    row shape itself)."""

    dimension_scores: dict[str, float] = Field(default_factory=dict)
    domain_fit_scores: dict[str, float] = Field(default_factory=dict)
    ranked_domains: list[Domain] = Field(default_factory=list)
    top_recommendation: Domain
    confidence_level: Literal["high", "moderate", "directional"]
    evidence_citations: dict[str, list[str]] = Field(default_factory=dict)
    summary_narrative: str
    strengths: list[str] = Field(default_factory=list)
    growth_areas: list[str] = Field(default_factory=list)
    extra: dict = Field(default_factory=dict)
