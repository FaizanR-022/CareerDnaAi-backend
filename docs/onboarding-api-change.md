# Onboarding API change — for Ali

**What changed:** `POST /api/v1/user/onboarding` now only accepts two fields.

## Before
```json
{
  "university": "MIT",
  "degree": "CS",
  "graduation_year": 2026,
  "career_interests": ["ux", "strategy"],
  "personality_results": { "trait": "high-openness" },
  "chosen_field": "product_manager",
  "self_assessment": [
    { "question": "Comfortable with ambiguity?", "score": 4 }
  ]
}
```

## After
```json
{
  "chosen_field": "product_manager",
  "self_assessment": [
    { "question": "Comfortable with ambiguity?", "score": 4 }
  ]
}
```

## Response (unchanged)
```json
{
  "success": true,
  "data": {
    "questions": [
      {
        "question": "Which document typically defines the success metrics for a new feature?",
        "options": ["PRD", "Postmortem", "Style guide", "Changelog"],
        "correct_option_index": 0
      }
      // ...5 total
    ]
  }
}
```
Always exactly 5 questions, each with 4 options and `correct_option_index` (0-based) so you can grade client-side and pick difficulty entirely on your end — backend never sees or stores the grading result.

## Why
You flagged that `university`/`degree`/`graduation_year`/`career_interests` were being asked for twice — they're already collected at signup (`POST /api/v1/auth/signup`), so onboarding didn't need to ask again. `personality_results` is dropped too — it had no signup equivalent and wasn't being used anywhere downstream.

**Bottom line: `chosen_field` and `self_assessment` are the only two things onboarding ever actually needed.** They're used to generate the 5 calibration MCQs in the response — nothing in the onboarding request gets persisted to the database at all now.

## What you need to change
Drop `university`, `degree`, `graduation_year`, `career_interests`, and `personality_results` from whatever payload your onboarding screen sends to this endpoint. Everything else — response shape (5 MCQs, same format as before), auth (Bearer token), status codes — is unchanged.

If your onboarding flow still collects university/degree/grad year/interests as UI steps, that's fine — just send them at signup instead (or via `PATCH /api/v1/users/me` if you need to update them after account creation).
