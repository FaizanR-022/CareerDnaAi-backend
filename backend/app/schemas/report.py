from typing import Literal

from pydantic import BaseModel

from app.schemas.agent_contracts import Domain


class ReportGenerateRequest(BaseModel):
    simulation_session_ids: list[str]


class CareerDnaReportResponse(BaseModel):
    id: str
    user_id: str
    dimension_scores: dict[str, float]
    domain_fit_scores: dict[str, float]
    ranked_domains: list[Domain]
    top_recommendation: Domain
    confidence_level: Literal["high", "moderate", "directional"]
    evidence_citations: dict[str, list[str]]
    summary_narrative: str
    strengths: list[str]
    growth_areas: list[str]
    simulation_session_ids: list[str]
    pdf_url: str | None = None
    version: int
    generated_at: str
