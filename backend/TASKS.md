# CareerDNA AI — Backend Completion Tasks

_Last updated: 2026-07-10 · Owner: Faizan (core backend)_

## Context

The simulation engine is being rebuilt to generate scenes dynamically, one
at a time, via the agent layer (Shayan/Ayesha's LLM code — being fully
revamped on their end), instead of loading static, pre-authored scenario
files. Core backend owns the session/scene orchestration API, its database
schema, and the admin dashboard — never the scene-generation, evaluation,
or report-narrative logic itself, which is called into rather than
reimplemented.

The old `director.py`-based flow (legacy `sessions` table, `session_service.py`,
`/session/*` and `/report/*` routers) was always temporary demo scaffolding.
**It has now been fully deleted from core backend** — see Status below.
Frontend (Ali) is being re-integrated from scratch next week against the
new `/simulations/*` flow; only the login/signup calls stay as they are.

## Status so far

**Domain naming — done.** One canonical set of domain keys applied
everywhere: `product_manager`, `sqa_engineer`, `data_analyst`,
`frontend_engineer`, `backend_engineer`.

**Database schema — drafted, not yet applied to Supabase.** `database/schema.sql`:
- **Active**: `universities`, `degrees`, `users`, `user_profiles`,
  `refresh_tokens`, `career_dna_reports`, `simulation_sessions`,
  `simulation_scenes`, `scene_evaluations`, `stakeholder_trust`, `npc_memory`.
- **Disabled** (commented out, kept for reference — confirmed none were ever
  written to, so nothing was lost): `sessions`, `scores`, `decisions_log`.
- Two legacy dashboard views removed, replaced by `simulation_student_progress`
  / `simulation_admin_overview`.
- `career_dna_reports.sessions_included` renamed to `simulation_session_ids`
  — this naming gap is now moot, see task 9 below (redesigned around a
  clean new contract instead of matching the old agent files' shape).
- File-level change only — **schema.sql has not been run against the live
  Supabase instance yet.** (Needs a full `DROP SCHEMA public CASCADE` +
  recreate first, since enum values changed — can't just re-run against
  the existing instance.)

**Legacy flow — fully deleted (2026-07-09).** `app/services/session_service.py`,
`app/api/v1/sessions.py`, `app/repositories/sessions.py`, `app/schemas/session.py`,
`app/services/report_service.py`, `app/api/v1/reports.py`,
`app/repositories/reports.py`, `app/schemas/report.py`, and
`tests/test_pm_e2e.py` are all removed. `main.py` no longer registers the
old `sessions`/`reports` routers. Verified: no other code imported any of
these (checked before deleting), test suite passes (19/19), app imports and
builds cleanly (9 routes registered). **`app/agents/director.py`,
`career_fit_agent.py`, `report_agent.py` were left untouched** — still
Shayan/Ayesha's files, just no longer called by anything in core backend
right now.

**Contract module (`app/schemas/agent_contracts.py`) — built.**
`SceneGenerationContext`/`SceneContent` (scene generation),
`EvaluationContext`/`EvaluationResult` (response evaluation). Domain values
use the settled full names. Reviewed and correct.

**Mock agent layer — built.** `app/services/mock_agent.py` (deterministic
fake scene/evaluation generation) + `app/services/agent_client.py`
(mock/real dispatch via `settings.agent_layer_impl`). Reviewed and correct.

**Repositories — built.** `simulation_sessions.py`, `simulation_scenes.py`,
`scene_evaluations.py`, `npc_state.py`, `user_profile.py`. All using the
shared `execute_or_503` helper (`app/repositories/__init__.py`) — real
Supabase failures surface as a clean 503 instead of silently degrading to
the memory fallback (that memory fallback is reserved for "Supabase not
configured" only). Reviewed and correct.

**`simulation_service.py` — built.** start / submit-response / next-scene /
current-scene / state / list-mine. Already proactively handles most of task
13's edge cases (already-evaluated scene, next-scene-before-evaluation,
already-completed session, scene-number mismatch). Reviewed and correct.

**`app/api/v1/simulations.py` — built, wired into `main.py`.** Response
models added (`SceneResponse`, `SubmitResponseResponse`, `SceneProgress`,
`SimulationStateResponse`, `SimulationSessionSummary`), composing
`agent_contracts.py` types rather than duplicating fields. Reviewed and
correct.

**Report orchestration (task 9) — built.** Clean new contract, not a reshape
to `career_fit_agent.py`/`report_agent.py`'s shape (per the "AI team
revamping their whole codebase" note) — `ScoredEvaluation`/
`SessionEvaluationSummary`/`FitReportContext`/`FitReportResult` added to
`agent_contracts.py`, `agent_client.generate_fit_report()` mock/real
dispatch, `app/repositories/career_dna_reports.py`,
`app/services/simulation_report_service.py`, `app/api/v1/simulation_reports.py`
(prefix `/reports`). `ranked_domains` deliberately not stored as its own
column — derived on read by sorting `domain_fit_scores`. Reviewed and
verified end-to-end (mock simulation → `/reports/generate` → real
`evidence_citations` pointing at actual `scene_evaluations.id` values).

**Tasks 1-9 all complete — now blocked on the AI team's revamp landing**
before tasks 11-13 (real integration) can proceed. Tasks 7 (schema apply)
and 10/14 (admin API, tests) don't depend on them and can still move.

**User module — rebuilt (2026-07-10).** Onboarding, update, and delete were
all incomplete/stale — see git history for the "wind up scattered things"
pass:
- `POST /user/onboarding` rewritten: saves the persistent profile fields
  (university, degree, personality_results, career_interests — unchanged
  behavior) and returns 5 AI-generated calibration MCQs (with answers) in
  the same response. New contract types in `agent_contracts.py`:
  `QuestionScore`, `MCQQuestion`, `MCQGenerationContext`,
  `MCQGenerationResult`; `agent_client.generate_mcqs()` mock/real dispatch,
  same pattern as the other three. `chosen_field`/`self_assessment` (the
  client's dynamic, SSR-generated self-assessment form) are used only to
  build the MCQ request context — **never persisted**. Client scores the
  MCQs and assigns difficulty itself; backend never sees or stores it.
- `user_profiles`' five `self_rated_*` columns: **not disabled** (unlike
  `scores`/`decisions_log`/`sessions`) — kept, given `DEFAULT 3 NOT NULL`
  instead, since `get_self_rating()`/`UserProfileSnippet.self_rating` in
  the live scene-generation path (`simulation_service._get_profile_snippet`)
  still reads them for arbitrary domains and would 503 on every
  `/simulations/start`/`next-scene` call if the columns went away. Safer
  than disabling — zero changes needed to the simulation flow.
  `save_onboarding()` omits these keys from its upsert now (doesn't
  overwrite existing values with the default on a later update).
- `PATCH /users/me` — partial update (`full_name`, `university`, `degree`,
  `graduation_year`, `core_interests`), new `UpdateUserRequest` schema
  with real `Field` validation. Deliberately excludes email/password —
  those need dedicated re-auth flows, don't exist as endpoints, flagged as
  a gap not built here.
- `DELETE /users/{user_id}` — soft delete (`is_active=false`) +
  `revoke_all_user_tokens()` so existing sessions die immediately, not at
  token expiry. Verified `auth_service.signin()` already checks
  `is_active` (403 "Account is disabled") — confirmed via live test:
  signup → delete → signin correctly blocked.
- All three endpoints live-tested end-to-end (signup → onboarding →
  MCQs returned; signup → update → delete → signin blocked), not just
  unit-verified. Test suite still 19/19, app builds cleanly (10 routes).

A shareable schema report and an architecture/workflow report both exist as
Claude Artifacts for mentor/team review (ask Faizan for links) — this file
is the implementation checklist, those are the presentation versions.

## Task checklist

1. [x] Draft `app/schemas/agent_contracts.py`.
2. [ ] Share the contract draft with Shayan/Ayesha — confirm field shapes,
   entry function name(s)/signatures for scene generation and evaluation,
   `npc_state_updates` shape.
3. [x] Build `app/services/mock_agent.py` + `app/services/agent_client.py`.
4. [x] Build repositories for the new tables.
5. [x] Build `app/services/simulation_service.py`.
6. [x] Build `app/api/v1/simulations.py`, wire into `app/main.py`.
7. [ ] **Apply `database/schema.sql` to Supabase** (full reset required —
   see Status above). Blocking real end-to-end testing.
8. [ ] Manual end-to-end walk against the mock — start → response →
   next-scene → ... → final scene → completed. Confirm `stakeholder_trust`/
   `npc_memory` rows populate correctly.
9. [x] Report orchestration — clean new contract, built (see Status above).
10. [ ] Admin API — `require_admin` dependency in `app/core/auth.py`,
    `app/api/v1/admin.py` + `app/services/admin_service.py`: list students,
    list/filter sessions, per-student drill-down, backed by
    `simulation_admin_overview`.
11. [ ] Swap `agent_client` from mock to real once Shayan/Ayesha's functions
    (scene gen, evaluation, and now fit-report per task 9) are ready. Handle
    their failure/timeout cases without corrupting session state.
12. [ ] Re-walk the full manual flow live against the real agent layer.
13. [ ] Edge-case pass — most of this is already handled in
    `simulation_service.py` (see Status); remaining: generating a report for
    an incomplete or another user's session.
14. [ ] Automated tests — repository CRUD (memory-fallback mode), full-flow
    integration test against the mock, admin endpoint auth tests.
15. [x] ~~Retire the legacy flow~~ — done 2026-07-09 (see Status above).
16. [ ] Final demo dry-run — full simulation, report generation, admin
    dashboard.

## Migrations (separate track, mentor-requested)

Alembic + SQLAlchemy Core setup for schema migrations, replacing the
hand-edit-`schema.sql`-and-reset workflow going forward. Scoped to
migrations only for now — transactions (e.g. making `submit_response()`'s
multi-table write sequence atomic) are a deferred follow-up, likely via the
same SQLAlchemy engine once it exists. Not started yet — user is handling
this separately, own timeline.

## Notes for whoever picks this up

- Don't edit anything under `app/agents/` or `scenarios/` without explicit
  sign-off — that's Shayan/Ayesha's (and Hassan's, for scenario content)
  territory, even though they're mid-revamp. The "free hand" the user has
  is about not needing to match those files' *current* shapes when
  designing new backend contracts — it is not permission to edit/delete
  their files.
- Legacy `/session/*` and `/report/*` flows are gone — don't try to
  resurrect or reference them.
- Known pre-existing bug in the (untouched) agent layer, not in scope here:
  `scenarios/sqa_engineer/sample.json` is a 0-byte file that crashes
  `director.py`'s scenario loader if it's ever invoked for an SQA session.
  Left alone per instruction.
