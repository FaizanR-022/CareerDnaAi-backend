from typing import Literal

from pydantic import BaseModel, Field

Domain = Literal[
    "product_manager", "sqa_engineer", "data_analyst", "frontend_engineer", "backend_engineer"
]
Difficulty = Literal["easy", "medium", "hard"]
Sentiment = Literal["positive", "neutral", "negative"]
ResponseFormat = Literal["free_text", "structured", "code", "interactive", "interactive_workspace"]


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
    isAudio: bool | None = None


class DataExplorerInteractive(BaseModel):
    editor_type: Literal["pipeline_config"] = "pipeline_config"
    available_imputation_strategies: list[str] = Field(default=["impute_mean", "drop_rows", "impute_zero"])
    available_duplicate_handling: list[str] = Field(default=["keep_first", "keep_last", "drop_all"])

class SqlEditorInteractive(BaseModel):
    editor_type: Literal["sql"] = "sql"
    initial_query: str | None = None

class PythonEditorInteractive(BaseModel):
    editor_type: Literal["python"] = "python"
    initial_code: str | None = None

class InsightsConsoleInteractive(BaseModel):
    editor_type: Literal["insights"] = "insights"
    hypothesis_options: list[str] = Field(default=["hyp_divergence", "hyp_seasonality", "hyp_bot_traffic"])

InteractiveConfig = dict | DataExplorerInteractive | SqlEditorInteractive | PythonEditorInteractive | InsightsConsoleInteractive

# --- DA Scene 1 Specific Schemas ---
class TableRow(BaseModel):
    index: str | int = "0"
    Timestamp: str
    Ticker: str
    Volume: int | float | str
    RSI: int | float | str | None = "null"
    Type: str
    issues: str = Field(description="String indicating row status, e.g., 'OK' or 'Error: Null RSI'")

class PipelineDropdown(BaseModel):
    options: list[str]
    correct: str

class PipelineConfig(BaseModel):
    null_handling: PipelineDropdown
    duplicate_handling: PipelineDropdown

class DataExplorerTask(BaseModel):
    problem_statement: str = Field(description="Write a 2-sentence scenario. Example: 'The RSI column is missing data due to sensor timeout. Fix it using imputation.'")
    flagged_constraints: list[str]
    schema_map: dict[str, str] = Field(default={"Timestamp": "VARCHAR", "Ticker": "VARCHAR", "Volume": "INTEGER", "RSI": "INTEGER", "Type": "VARCHAR"}, alias="schema", description="A flat dictionary of column names to SQL types.")
    pipeline_config: PipelineConfig
    table_data: list[TableRow] = Field(min_length=3, max_length=25, description="A JSON array of 3 to 20 objects. Ensure every object includes the 'issues' field.")

class InteractiveTasks(BaseModel):
    data_explorer: DataExplorerTask

class DAContextData(BaseModel):
    interactive_tasks: InteractiveTasks
    active_npcs: list[dict | str] = Field(default_factory=list)
    scene_type: str = ""


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
    prompt_for_response: str = Field(default="Please complete the active task to proceed to the next scene.")
    hint: str | None = None
    is_final_scene: bool = False
    voice_memo: dict | None = None
    interactive_config: dict | None = None
    extra: dict = Field(default_factory=dict)


class DAScene1Content(SceneContent):
    context_data: DAContextData
    # Override fields that use Union/Optional to prevent Groq API 'anyOf' validation crashes
    interactive_config: dict = Field(default_factory=dict)
    response_choices: list[str] = Field(default_factory=list)
    hint: str = ""

# --- DA Scene 3 Specific Schemas ---
class PythonValidation(BaseModel):
    required_functions: list[str]

class PythonSandboxTask(BaseModel):
    is_completed: bool = False
    problem_statement: str
    editor_type: Literal["python"] = "python"
    default_code: str
    helper_snippets: list[str]
    validation: PythonValidation

class AnomalyGuide(BaseModel):
    title: str
    institutional_divergence: str
    rsi_momentum: str

class SidebarGuides(BaseModel):
    anomaly_guide: AnomalyGuide

class DA3InteractiveTasks(BaseModel):
    python_sandbox: PythonSandboxTask

class DA3ContextData(BaseModel):
    interactive_tasks: DA3InteractiveTasks
    sidebar_guides: SidebarGuides
    active_npcs: list[dict | str] = Field(default_factory=list)
    scene_type: str = ""

class DAScene3Content(SceneContent):
    context_data: DA3ContextData
    interactive_config: dict = Field(default_factory=dict)
    response_choices: list[str] = Field(default_factory=list)
    hint: str = ""


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

# --- Frontend Engineer Schemas ---

class MockupOptionMetrics(BaseModel):
    contrast_ratio: str

class MockupOption(BaseModel):
    id: str
    title: str
    is_accessible: bool
    metrics: MockupOptionMetrics

class DesignReviewTask(BaseModel):
    is_completed: bool = False
    problem_statement: str
    requires_reason: bool = True
    options: list[MockupOption]

class AvailableBlock(BaseModel):
    id: str
    label: str

class WireframeBuilderTask(BaseModel):
    is_completed: bool = False
    problem_statement: str
    available_blocks: list[AvailableBlock]
    canvas_slots: int
    expected_stack_sequence: list[str]

class CssVariableOption(BaseModel):
    current: str
    options: list[str]
    correct: str

class CssSandboxTask(BaseModel):
    is_completed: bool = False
    target_viewport: Literal["mobile"] = "mobile"
    viewport_width: Literal[375] = 375
    problem_statement: str
    raw_css: str
    editable_variables: dict[str, CssVariableOption]

# FE Common Context
class FEContextData(BaseModel):
    active_npcs: list[dict | str] = Field(default_factory=list)
    scene_type: str = ""

# FE LLM Generation
class LLMSceneOutput(BaseModel):
    title: str
    narrative: str
    messages: list[SceneMessage]
    characters: list[Character]

# Scene 1: Design Review
class FEScene1InteractiveConfig(BaseModel):
    active_tabs: list[str] = Field(default_factory=list)
    design_review: DesignReviewTask

class FEScene1Content(SceneContent):
    context_data: FEContextData = Field(default_factory=FEContextData)
    interactive_config: FEScene1InteractiveConfig

# Scene 2: Design Review + Wireframe
class FEScene2InteractiveConfig(BaseModel):
    active_tabs: list[str] = Field(default_factory=list)
    design_review: DesignReviewTask
    wireframe_builder: WireframeBuilderTask

class FEScene2Content(SceneContent):
    context_data: FEContextData = Field(default_factory=FEContextData)
    interactive_config: FEScene2InteractiveConfig

# Scene 3: Wireframe + CSS (Mobile)
class FEScene3InteractiveConfig(BaseModel):
    active_tabs: list[str] = Field(default_factory=list)
    wireframe_builder: WireframeBuilderTask
    css_sandbox: CssSandboxTask

class FEScene3Content(SceneContent):
    context_data: FEContextData = Field(default_factory=FEContextData)
    interactive_config: FEScene3InteractiveConfig

# Scene 4: Design Review + CSS (Mobile)
class FEScene4InteractiveConfig(BaseModel):
    active_tabs: list[str] = Field(default_factory=list)
    design_review: DesignReviewTask
    css_sandbox: CssSandboxTask

class FEScene4Content(SceneContent):
    context_data: FEContextData = Field(default_factory=FEContextData)
    interactive_config: FEScene4InteractiveConfig
