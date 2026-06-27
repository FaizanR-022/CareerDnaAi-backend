"""
Report Agent
Generates Career DNA Report narrative from structured fit scores.
Uses Groq LLM for narrative generation only.
All scoring logic lives in career_fit_agent.py — this agent only narrates.
"""

import json
from langchain_core.messages import HumanMessage
from agents.director import get_llm


def generate_report_narrative(fit_data: dict) -> dict:
    """
    Takes structured fit data from career_fit_agent.generate_fit_report_data()
    and generates Career DNA Report narrative using Groq.

    Args:
        fit_data: dict from generate_fit_report_data() containing
                  domain_fit_scores, ranked_domains, dimension_scores,
                  confidence_level, evidence_citations, user_id

    Returns:
        Complete report dict ready to insert into career_dna_reports table
    """
    llm = get_llm(model="llama-3.3-70b-versatile", temperature=0.4)

    top_domain = fit_data.get("top_domain", "unknown")
    ranked = fit_data.get("ranked_domains", [])
    dim_scores = fit_data.get("dimension_scores", {})
    fit_scores = fit_data.get("domain_fit_scores", {})
    confidence = fit_data.get("confidence_level", "directional")
    evidence = fit_data.get("evidence_citations", {})
    domains_simulated = fit_data.get("domains_simulated", [])

    domain_labels = {
        "pm": "Product Manager",
        "sqa": "SQA Engineer",
        "data_analyst": "Data Analyst",
        "frontend": "Frontend Engineer",
        "backend": "Backend Engineer"
    }

    prompt = f"""You are generating a Career DNA Report for a CS student who \
completed career simulations on CareerDNA AI. Write honest, \
evidence-grounded career guidance based only on what their \
simulation decisions showed. Do not make general claims about \
personality — only reference what was observed in the session.

STUDENT DIMENSION SCORES (0-100, higher is better):
{json.dumps(dim_scores, indent=2)}

DOMAIN FIT SCORES (0-100):
{json.dumps({domain_labels.get(k, k): v for k, v in fit_scores.items()}, indent=2)}

TOP RECOMMENDED DOMAIN: {domain_labels.get(top_domain, top_domain)}
DOMAINS ACTUALLY SIMULATED: {[domain_labels.get(d, d) for d in domains_simulated]}
CONFIDENCE LEVEL: {confidence}

STRICT RULES:
- Never say "you ARE X" — say "your decisions in this session showed..."
- Always frame as session-based, not a permanent verdict
- Be honest about lower scores as growth areas, not failures
- Summary must be exactly 3 sentences
- Strengths must reference specific behavioral patterns from the scores
- Growth areas must include one actionable suggestion each

Return ONLY valid JSON, no markdown fences, no preamble, no explanation:
{{
  "summary_narrative": "3 sentences based on session behavior",
  "strengths": [
    "specific strength 1 grounded in dimension scores",
    "specific strength 2 grounded in dimension scores",
    "specific strength 3 grounded in dimension scores"
  ],
  "growth_areas": [
    "growth area 1 with actionable suggestion",
    "growth area 2 with actionable suggestion"
  ],
  "top_recommendation": "{top_domain}",
  "second_recommendation": "{ranked[1] if len(ranked) > 1 else 'none'}",
  "recommendation_reasoning": "2 sentences explaining why top domain fits this student",
  "confidence_statement": "1 honest sentence about how much to trust this result"
}}"""

    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        raw = response.content.strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        narrative = json.loads(raw)
    except Exception as e:
        print(f"[ReportAgent] LLM error: {e} — using fallback narrative")
        narrative = {
            "summary_narrative": (
                f"Based on your simulation session, your decisions suggest "
                f"a potential fit for {domain_labels.get(top_domain, top_domain)}. "
                f"Your strongest dimension was "
                f"{max(dim_scores, key=dim_scores.get) if dim_scores else 'analytical reasoning'}. "
                f"This is a {confidence} estimate based on your completed sessions."
            ),
            "strengths": [
                "Decision-making under ambiguity",
                "Stakeholder communication clarity",
                "Structured analytical reasoning"
            ],
            "growth_areas": [
                "Attention to edge cases — practice reviewing specs for missing details",
                "Decisiveness under time pressure — try setting personal deadlines"
            ],
            "top_recommendation": top_domain,
            "second_recommendation": ranked[1] if len(ranked) > 1 else "none",
            "recommendation_reasoning": (
                "Your behavioral patterns align with this domain's core requirements. "
                "Consider exploring it further through real projects or internships."
            ),
            "confidence_statement": (
                f"This is a {confidence} estimate — completing more domain "
                f"simulations will increase accuracy."
            )
        }

    return {
        "user_id": fit_data.get("user_id"),
        "dim_analytical":    dim_scores.get("analytical_reasoning", 0),
        "dim_ambiguity":     dim_scores.get("ambiguity_tolerance", 0),
        "dim_communication": dim_scores.get("communication_clarity", 0),
        "dim_attention":     dim_scores.get("attention_to_detail", 0),
        "dim_decisiveness":  dim_scores.get("decisiveness", 0),
        "domain_fit_scores": fit_scores,
        "summary_narrative": narrative.get("summary_narrative"),
        "strengths":         narrative.get("strengths", []),
        "growth_areas":      narrative.get("growth_areas", []),
        "top_recommendation": narrative.get("top_recommendation"),
        "confidence_level":  confidence,
        "evidence_citations": evidence,
        "sessions_included": fit_data.get("sessions_included", []),
        "pdf_url":  None,
        "version":  1
    }


def save_report_to_supabase(report_data: dict, supabase_client) -> str:
    """Save generated report to career_dna_reports table. Returns report ID."""
    try:
        result = (supabase_client
                  .table("career_dna_reports")
                  .insert(report_data)
                  .execute())
        return result.data[0]["id"] if result.data else None
    except Exception as e:
        print(f"[ReportAgent] Supabase save error: {e}")
        return None
