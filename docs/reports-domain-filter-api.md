# Reports API — new `domain` filter on GET /api/v1/reports

**What's new:** `GET /api/v1/reports` now accepts an optional `domain` query param to fetch the report for a user's latest completed simulation in a specific domain, instead of every report they've ever generated.

## Request

```
GET /api/v1/reports?domain=backend_engineer
Authorization: Bearer <token>
```

`domain` is optional. Valid values (exactly these five strings):

- `product_manager`
- `sqa_engineer`
- `data_analyst`
- `frontend_engineer`
- `backend_engineer`

Anything else returns a `422`.

## Response

Same shape either way — always a JSON array of report objects (`CareerDnaReportResponse[]`), never a bare object:

```json
[
  {
    "id": "5b1e...",
    "user_id": "9a02...",
    "dimension_scores": {
      "analytical_reasoning": 0.82,
      "ambiguity_tolerance": 0.61,
      "communication_clarity": 0.74,
      "attention_to_detail": 0.9,
      "decisiveness": 0.55
    },
    "domain_fit_scores": { "backend_engineer": 0.88, "data_analyst": 0.71 },
    "ranked_domains": ["backend_engineer", "data_analyst"],
    "top_recommendation": "backend_engineer",
    "confidence_level": "high",
    "evidence_citations": { "analytical_reasoning": ["scene_3 evaluation..."] },
    "summary_narrative": "...",
    "strengths": ["..."],
    "growth_areas": ["..."],
    "simulation_session_ids": ["sess_123"],
    "pdf_url": null,
    "version": 1,
    "generated_at": "2026-07-16T10:22:00Z"
  }
]
```

**Without `?domain=`** — the array contains every report the user has ever generated (unchanged from before).

**With `?domain=X`** — the array has at most one item: the report tied to the user's most recent *completed* simulation session in that domain.
- No completed session in that domain yet → `[]`
- Completed session exists but no report generated for it yet → `[]`
- Report exists → `[<that report>]`

Always check `.length` client-side rather than assuming an object — an empty array just means "nothing to show yet," not an error.

## Also new: duplicate report generation is now blocked

`POST /api/v1/reports` now returns `409 Conflict` if you try to generate a report for a session that already has one:

```json
{ "detail": "A report already exists for simulation session sess_123" }
```

If you hit this, call `GET /api/v1/reports?domain=X` (or `GET /api/v1/reports/{report_id}` if you already have the id) to fetch the existing report instead of retrying the POST.

## What you need to do

- To show "your latest backend-engineer report" (or any single-domain report) on a dashboard/profile screen, call `GET /api/v1/reports?domain=<domain>` and take `data[0]` if the array isn't empty.
- Keep handling `GET /api/v1/reports` (no param) as before for a "report history" list view.
- If your "generate report" button can be clicked more than once for the same session (double-click, retry after timeout), handle the `409` by treating it the same as success and fetching the existing report — don't show it as a hard error.
