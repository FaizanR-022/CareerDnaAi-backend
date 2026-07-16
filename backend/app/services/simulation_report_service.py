import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException

from app.core.auth import verify_self_or_admin, verify_session_ownership
from app.repositories import career_dna_reports as reports_repo
from app.repositories import scene_evaluations, simulation_scenes, simulation_sessions
from app.schemas.agent_contracts import (
    Domain,
    EvaluationResult,
    FitReportContext,
    ScoredEvaluation,
    SessionEvaluationSummary,
)
from app.services import agent_client

logger = logging.getLogger(__name__)

DIM_COLUMN_MAP = {
    "analytical_reasoning": "dim_analytical",
    "ambiguity_tolerance": "dim_ambiguity",
    "communication_clarity": "dim_communication",
    "attention_to_detail": "dim_attention",
    "decisiveness": "dim_decisiveness",
}


def _build_session_summary(session: dict) -> SessionEvaluationSummary:
    scenes = simulation_scenes.list_scenes(session["id"])
    evaluations = {
        e["scene_id"]: e
        for e in scene_evaluations.list_evaluations_for_scenes([s["id"] for s in scenes])
    }

    scored = []
    for scene_row in scenes:
        eval_row = evaluations.get(scene_row["id"])
        if not eval_row or not eval_row.get("evaluation"):
            continue
        scored.append(
            ScoredEvaluation(
                scene_evaluation_id=eval_row["id"],
                scene_number=scene_row["scene_number"],
                result=EvaluationResult(**eval_row["evaluation"]),
            )
        )

    return SessionEvaluationSummary(
        simulation_session_id=session["id"],
        domain=session["domain"],
        difficulty=session["difficulty"],
        evaluations=scored,
    )


def _row_to_response(row: dict) -> dict:
    dimension_scores = {
        dim: row[col] for dim, col in DIM_COLUMN_MAP.items() if row.get(col) is not None
    }
    domain_fit_scores = row.get("domain_fit_scores") or {}
    ranked_domains = sorted(domain_fit_scores, key=domain_fit_scores.get, reverse=True)

    return {
        "id": row["id"],
        "user_id": row["user_id"],
        "dimension_scores": dimension_scores,
        "domain_fit_scores": domain_fit_scores,
        "ranked_domains": ranked_domains,
        "top_recommendation": row.get("top_recommendation"),
        "confidence_level": row.get("confidence_level"),
        "evidence_citations": row.get("evidence_citations") or {},
        "summary_narrative": row.get("summary_narrative"),
        "strengths": row.get("strengths") or [],
        "growth_areas": row.get("growth_areas") or [],
        "simulation_session_ids": row.get("simulation_session_ids") or [],
        "pdf_url": row.get("pdf_url"),
        "version": row.get("version"),
        "generated_at": row.get("generated_at"),
    }


async def generate_report(current_user: dict, simulation_session_ids: list[str]) -> dict:
    sessions = []
    for session_id in simulation_session_ids:
        session = simulation_sessions.get_session(session_id)
        if not session:
            raise HTTPException(
                status_code=404, detail=f"Simulation session not found: {session_id}"
            )
        verify_session_ownership(session, current_user)
        sessions.append(session)

    completed = [s for s in sessions if s["status"] == "completed"]
    if not completed:
        raise HTTPException(status_code=400, detail="No completed sessions among the given IDs")

    for session in completed:
        if reports_repo.find_report_for_session(current_user["user_id"], session["id"]):
            raise HTTPException(
                status_code=409,
                detail=f"A report already exists for simulation session {session['id']}",
            )

    session_summaries = [_build_session_summary(s) for s in completed]
    ctx = FitReportContext(user_id=current_user["user_id"], sessions=session_summaries)
    result = await agent_client.generate_fit_report(ctx)

    row = {
        "id": str(uuid.uuid4()),
        "user_id": current_user["user_id"],
        **{
            DIM_COLUMN_MAP[dim]: value
            for dim, value in result.dimension_scores.items()
            if dim in DIM_COLUMN_MAP
        },
        "domain_fit_scores": result.domain_fit_scores,
        "summary_narrative": result.summary_narrative,
        "strengths": result.strengths,
        "growth_areas": result.growth_areas,
        "top_recommendation": result.top_recommendation,
        "confidence_level": result.confidence_level,
        "evidence_citations": result.evidence_citations,
        "simulation_session_ids": [s["id"] for s in completed],
        "pdf_url": None,
        "version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    saved = reports_repo.save_report(row)
    return _row_to_response(saved)


def get_report(report_id: str, current_user: dict) -> dict:
    row = reports_repo.get_report(report_id)
    if not row:
        raise HTTPException(status_code=404, detail="Report not found")
    verify_self_or_admin(row["user_id"], current_user, detail="Not your report")
    return _row_to_response(row)


def list_my_reports(current_user: dict, domain: Optional[Domain] = None) -> list[dict]:
    if domain:
        session = simulation_sessions.get_latest_session_for_domain(
            current_user["user_id"], domain, status="completed"
        )
        if not session:
            return []
        report = reports_repo.find_report_for_session(current_user["user_id"], session["id"])
        return [_row_to_response(report)] if report else []

    rows = reports_repo.list_reports_for_user(current_user["user_id"])
    return [_row_to_response(r) for r in rows]
