import logging

from fastapi import HTTPException

from app.agents.career_fit_agent import generate_fit_report_data
from app.agents.report_agent import generate_report_narrative
from app.repositories import reports as reports_repo
from app.repositories import sessions as sessions_repo

logger = logging.getLogger(__name__)


def generate_report(user_id: str, session_ids: list[str]) -> dict:
    sessions_data = []
    for sid in session_ids:
        state = sessions_repo.load_session(sid)
        if state and state.get("scores"):
            sessions_data.append({
                "domain": state["domain"],
                "scores": state["scores"],
                "decisions_log": state["decisions_log"],
                "session_id": sid,
            })

    if not sessions_data:
        raise HTTPException(
            status_code=404,
            detail="No valid completed sessions found for provided IDs",
        )

    fit_data = generate_fit_report_data(user_id, sessions_data)
    fit_data["sessions_included"] = session_ids

    report = generate_report_narrative(fit_data)
    report_id = reports_repo.save_report(report)

    return {
        "report_id": report_id,
        "report": report,
        "fit_scores": fit_data["domain_fit_scores"],
        "ranked_domains": fit_data["ranked_domains"],
        "confidence": fit_data["confidence_level"],
    }
