"""
Career Fit Agent
Career Simulator · Folio3 Internship Project
---------------------------------------------
Takes decisions_log from completed sessions and produces
ranked domain fit scores for the Career DNA Report.

No LLM needed — this is deterministic aggregation.
"""

from __future__ import annotations
from typing import Optional


# ─── DOMAIN WEIGHT PROFILES ──────────────────────────────────────────────────
# Each domain values certain dimensions more than others.
# These weights are authored, not computed.
# All weights in a profile must sum to 1.0

DOMAIN_PROFILES = {
    "pm": {
        "analytical_reasoning":   0.20,
        "ambiguity_tolerance":    0.30,
        "communication_clarity":  0.25,
        "attention_to_detail":    0.10,
        "decisiveness":           0.15,
    },
    "sqa": {
        "analytical_reasoning":   0.20,
        "ambiguity_tolerance":    0.10,
        "communication_clarity":  0.15,
        "attention_to_detail":    0.35,
        "decisiveness":           0.20,
    },
    "data_analyst": {
        "analytical_reasoning":   0.35,
        "ambiguity_tolerance":    0.20,
        "communication_clarity":  0.20,
        "attention_to_detail":    0.20,
        "decisiveness":           0.05,
    },
    "frontend": {
        "analytical_reasoning":   0.15,
        "ambiguity_tolerance":    0.20,
        "communication_clarity":  0.20,
        "attention_to_detail":    0.30,
        "decisiveness":           0.15,
    },
    "backend": {
        "analytical_reasoning":   0.30,
        "ambiguity_tolerance":    0.15,
        "communication_clarity":  0.15,
        "attention_to_detail":    0.25,
        "decisiveness":           0.15,
    },
}


# ─── MAIN FUNCTION ────────────────────────────────────────────────────────────

def compute_career_fit(dimension_scores: dict[str, float]) -> dict:
    """
    Given a student's dimension scores, compute fit scores for all 5 domains.

    Args:
        dimension_scores: dict of {dimension_name: float (0-100)}
            e.g. {"analytical_reasoning": 72.5, "ambiguity_tolerance": 65.0, ...}

    Returns:
        {
            "domain_fit_scores": {"pm": 74.2, "sqa": 68.1, ...},
            "ranked_domains": ["pm", "data_analyst", ...],   # best fit first
            "top_domain": "pm",
            "confidence_level": "high" | "moderate" | "directional",
            "dimension_scores": {...},   # passed through
        }
    """
    fit_scores = {}

    for domain, weights in DOMAIN_PROFILES.items():
        weighted_sum = 0.0
        weight_total = 0.0
        for dimension, weight in weights.items():
            score = dimension_scores.get(dimension, 0.0)
            if score > 0:  # only include dimensions that were actually scored
                weighted_sum += score * weight
                weight_total += weight

        if weight_total > 0:
            fit_scores[domain] = round(weighted_sum / weight_total, 1)
        else:
            fit_scores[domain] = 0.0

    ranked = sorted(fit_scores.keys(), key=lambda d: fit_scores[d], reverse=True)
    top_domain = ranked[0] if ranked else None

    # Confidence based on how many dimensions were scored
    scored_dims = sum(1 for v in dimension_scores.values() if v > 0)
    if scored_dims >= 4:
        confidence = "high"
    elif scored_dims >= 2:
        confidence = "moderate"
    else:
        confidence = "directional"

    return {
        "domain_fit_scores": fit_scores,
        "ranked_domains": ranked,
        "top_domain": top_domain,
        "confidence_level": confidence,
        "dimension_scores": dimension_scores,
    }


def aggregate_scores_from_sessions(sessions_data: list[dict]) -> dict[str, float]:
    """
    Aggregates dimension scores across multiple completed sessions.

    Args:
        sessions_data: list of session dicts, each with a "scores" key
            e.g. [{"domain": "pm", "scores": {"analytical_reasoning": 72, ...}}, ...]

    Returns:
        Aggregated dimension scores dict
    """
    totals: dict[str, list[float]] = {}

    for session in sessions_data:
        scores = session.get("scores", {})
        for dim, val in scores.items():
            if val and val > 0:
                if dim not in totals:
                    totals[dim] = []
                totals[dim].append(float(val))

    # Average across sessions
    return {
        dim: round(sum(vals) / len(vals), 1)
        for dim, vals in totals.items()
        if vals
    }


def build_evidence_citations(decisions_log: list[dict]) -> dict[str, list[str]]:
    """
    Maps each dimension to the decision IDs that contributed most to it.
    Used by Report Agent to cite specific moments in the Career DNA Report.

    Returns:
        {"analytical_reasoning": ["decision_id_1", "decision_id_2"], ...}
    """
    citations: dict[str, list[str]] = {
        "analytical_reasoning": [],
        "ambiguity_tolerance": [],
        "communication_clarity": [],
        "attention_to_detail": [],
        "decisiveness": [],
    }

    for i, decision in enumerate(decisions_log):
        dim_scores = decision.get("dimension_scores", {})
        decision_ref = decision.get("id", f"decision_{i}")

        for dim, score in dim_scores.items():
            if score and score >= 65 and dim in citations:
                citations[dim].append(decision_ref)

    # Keep top 3 evidence points per dimension
    return {dim: refs[:3] for dim, refs in citations.items()}


# ─── FASTAPI ENDPOINT HELPER ──────────────────────────────────────────────────

def generate_fit_report_data(user_id: str, sessions: list[dict]) -> dict:
    """
    Full pipeline: sessions → aggregated scores → fit scores → evidence citations.
    Called by Report Agent or directly from the API.

    Args:
        user_id: the student's user ID
        sessions: list of completed session dicts from Postgres

    Returns:
        Complete fit report data ready for the Report Agent to narrate.
    """
    # Aggregate dimension scores
    dimension_scores = aggregate_scores_from_sessions(sessions)

    # Compute fit scores
    fit_result = compute_career_fit(dimension_scores)

    # Build evidence citations
    all_decisions = []
    for session in sessions:
        all_decisions.extend(session.get("decisions_log", []))
    evidence = build_evidence_citations(all_decisions)

    return {
        "user_id": user_id,
        "domain_fit_scores": fit_result["domain_fit_scores"],
        "ranked_domains": fit_result["ranked_domains"],
        "top_domain": fit_result["top_domain"],
        "confidence_level": fit_result["confidence_level"],
        "dimension_scores": dimension_scores,
        "evidence_citations": evidence,
        "sessions_count": len(sessions),
        "domains_simulated": list({s["domain"] for s in sessions}),
    }
