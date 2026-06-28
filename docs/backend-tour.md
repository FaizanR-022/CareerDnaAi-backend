# CareerDNA AI — Guided Backend Tour

This document walks through every file and folder in the backend, explaining what it owns, why it exists, and how it connects to the rest of the system.

---

## The Big Picture

A student opens the app, picks a domain (e.g. Product Manager), and starts a simulation. Behind every action they take, the backend does roughly this:

```
Student sends a message
        │
        ▼
FastAPI router receives POST /session/action
        │
        ▼
session_service.handle_action() loads the session state,
injects the student's message, and runs it through the LangGraph director
        │
        ▼
Director classifies the action → scores it (LLM) → generates NPC reply (LLM)
        │
        ▼
Updated state is saved to Supabase (or memory fallback)
        │
        ▼
Response returned to frontend: NPC dialogue, score update, UI events
```

Everything in the codebase exists to make this flow clean, testable, and maintainable.

---

## Top-Level Layout

```
backend/
├── app/          ← the application package
├── tests/        ← pytest test suite
├── scenarios/    ← JSON scenario content (Hassan's — do not touch)
├── database/     ← schema.sql for Supabase
├── main.py       ← uvicorn entry point
├── requirements.txt
├── requirements-dev.txt
└── pytest.ini
```

---

## `app/main.py` — Entry Point & App Factory

**What it does:** Creates the FastAPI application, registers CORS middleware, initialises Supabase, and wires all the routers together.

**Key functions:**
- `create_app()` — factory function that returns a configured `FastAPI` instance. Called once at startup.
- The module-level `app = create_app()` is what uvicorn imports.

**Why a factory function?** It keeps startup side-effects (Supabase init, logging setup) inside an explicit call rather than scattered at module level. Easier to test and reason about.

**Start command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

---

## `app/core/` — Cross-Cutting Concerns

This layer owns things that every other layer needs: configuration, logging format, and authentication. Nothing here knows about business logic or database tables.

### `config.py`

Uses `pydantic-settings` to load and validate environment variables from `.env`. Every env var the app needs is declared here with its type and default.

```python
class Settings(BaseSettings):
    supabase_url: str = ""
    supabase_key: str = ""
    frontend_url: str = ""
    llm_provider: str = "groq"
    groq_api_key: str = ""
    openrouter_api_key: str = ""
```

`get_settings()` is decorated with `@lru_cache` so the `.env` file is only read once per process, not on every request.

**Who uses it:** `db/client.py`, `agents/llm.py`, `main.py`

### `logging.py`

`setup_logging()` configures the root Python logger once at startup (called from `main.py`). After this, every module can do `logger = logging.getLogger(__name__)` and get structured log output with timestamps and log levels.

**Why not `print()`:** `print()` has no timestamps, no severity levels, and can't be filtered or routed. `logging` gives you all three for free.

### `auth.py`

Contains the `get_current_user()` FastAPI dependency. Every protected endpoint declares `current_user: dict = Depends(get_current_user)` in its signature.

**Behaviour:**
- If Supabase is not configured (dev mode): returns a hardcoded dev user — no auth required.
- If Supabase is configured: validates the `Authorization: Bearer <token>` JWT against Supabase Auth.
- Raises `HTTP 401` if the token is missing or invalid.

Also contains `verify_session_ownership()` — a helper that raises `HTTP 403` if the session doesn't belong to the current user.

---

## `app/db/` — Database Client

### `client.py`

Owns the Supabase client singleton. Two functions:

- `init_supabase()` — called once during app startup (`main.py → create_app()`). Reads credentials from Settings, creates the client, stores it in a module-level variable.
- `get_supabase()` — returns the client (or `None` if not configured). Called by repositories when they need to query Supabase.

**Why a singleton:** Creating a new Supabase client on every request is expensive. One client per process, reused across all requests.

**Memory-only mode:** If `SUPABASE_URL` / `SUPABASE_KEY` are not set (or left as placeholders), `init_supabase()` skips client creation and logs a warning. The repositories fall back to an in-memory dict — useful for local development without a real Supabase project.

---

## `app/schemas/` — Pydantic Models

These are the data contracts between the HTTP layer and the rest of the app. Nothing business-logic-related lives here — just shape definitions.

| File | Contains |
|------|----------|
| `session.py` | `StartSessionRequest`, `ActionRequest` |
| `user.py` | `OnboardingRequest` |
| `report.py` | `ReportRequest` |

**Why separate from the routers:** Schemas are reusable — a service or test can construct a request object directly without going through HTTP. Keeping them in their own files makes them easy to find and import.

---

## `app/repositories/` — Data Access Layer

**Rule:** ALL Supabase access lives in this folder. No other layer is allowed to call `supabase.table(...)` directly.

Each file corresponds to one or more related database tables.

### `sessions.py`

The most complex repository. Owns three functions:

**`save_session(session_id, state)`**
- If Supabase is available: upserts the session row. The `scene_state` JSONB column holds scores, decisions_log, stakeholder_trust, npc_states, and sprint_progress as a single blob (avoids needing to update 5 tables on every action).
- If Supabase throws: logs the error and falls back to the in-memory dict.
- If no Supabase: writes to the in-memory dict.

**`load_session(session_id)`**
- If Supabase is available: fetches the row, reconstructs a full `SimulationState` by calling `create_initial_state()` and then overwriting the fields that were persisted.
- Falls back to in-memory if Supabase fails or isn't configured.

**`get_incomplete_sessions(user_id)`**
- Returns all `active` or `paused` sessions for a user.
- In-memory mode returns a filtered list from the in-process dict.
- Supabase mode runs a filtered query.

### `users.py`

**`save_onboarding(user_id, data)`**
- Updates the `users` table (university field).
- Upserts the `user_profiles` table (personality results, self-rated scores).

### `reports.py`

**`save_report(report_data)`**
- Inserts a completed Career DNA Report into `career_dna_reports`.
- Returns the new row's UUID (used by the API response).
- Returns `None` if Supabase is not configured (report is still returned to caller, just not persisted).

---

## `app/agents/` — AI Agents

The AI layer. Agents are called by services, never by routers or repositories.

### `llm.py`

`get_llm(model, temperature)` — the single factory function for creating LLM instances.

Reads `LLM_PROVIDER` from settings:
- `"groq"` → returns a `ChatGroq` instance (primary)
- `"openrouter"` → returns a `ChatOpenAI` pointed at OpenRouter's API (fallback)

**Why extracted here:** Previously `get_llm()` lived inside `director.py`. `report_agent.py` was importing it from there, creating a coupling between two unrelated agents. Moving it to `llm.py` gives both agents a neutral shared dependency.

### `director.py`

The core simulation engine. A LangGraph state machine with 4 nodes:

```
classify_node (deterministic, no LLM)
       │
       ├── branch_decision_* → score_node (LLM judge)
       │                              │
       │                              ├── (most decisions) → npc_node (LLM)
       │                              └── (blind accept)  → scene_transition_node
       │
       ├── npc_message_* → npc_node (LLM)
       │
       └── scene_complete → scene_transition_node (deterministic)
```

**Nodes:**
| Node | LLM? | What it does |
|------|------|--------------|
| `classify_node` | No | Keyword-matches the student's action to an `action_type`. Fast, deterministic, no API cost. |
| `score_node` | Yes (Groq) | Sends the action to the LLM as a scoring judge. Returns dimension scores (0–100) and behavioural flags. Updates the running average scores in state. |
| `npc_node` | Yes (Groq) | Generates in-character NPC dialogue. Uses the NPC's personality config, current trust level, and hard constraints (sprint capacity facts). Updates NPC memory and stakeholder trust. |
| `scene_transition_node` | No | Computes average score, selects next scene variant (stretch/standard/support), updates session status. |

**Scenario loading:** `load_full_scenario_config(domain)` reads all `scene_*.json` and NPC JSON files from `scenarios/{domain}/` at session start. The config is stored in `SimulationState.scenario_config` for the duration of the session — no repeated file I/O per action.

**`SimulationState`:** A `TypedDict` that carries every piece of session state through the graph. LangGraph nodes receive the current state and return a partial dict of updates.

**`create_initial_state()`:** Called by `session_service.start_session()` to create a fresh state for a new session. Loads scenario config, initialises trust levels from NPC JSON files.

**`build_director()`:** Compiles the LangGraph graph. Called once at module import time in `session_service.py`.

### `career_fit_agent.py`

Purely deterministic — no LLM. Takes the student's final dimension scores across all completed sessions and produces ranked domain fit scores.

**Functions:**
- `aggregate_scores_from_sessions(sessions)` — averages dimension scores across multiple sessions
- `compute_career_fit(dimension_scores)` — multiplies each dimension by domain-specific weights (defined in `DOMAIN_PROFILES`) to produce a fit score per domain
- `build_evidence_citations(decisions_log)` — maps each dimension to the specific decisions that scored highest in that dimension (used to ground the narrative report)
- `generate_fit_report_data(user_id, sessions)` — the full pipeline: aggregate → fit → citations → combined output dict

**`DOMAIN_PROFILES`:** The weight table that defines which dimensions matter most for each career domain. E.g. PM weights `ambiguity_tolerance` (0.30) most; SQA weights `attention_to_detail` (0.35) most.

### `report_agent.py`

LLM-powered narrative generation. Takes the structured output from `career_fit_agent.generate_fit_report_data()` and turns it into the human-readable Career DNA Report.

`generate_report_narrative(fit_data)`:
- Builds a prompt with dimension scores, domain fit scores, top recommendation, and strict output rules (e.g. "never say 'you ARE X'")
- Calls Groq to generate a JSON narrative (summary, strengths, growth_areas, recommendation_reasoning)
- Has a full fallback narrative if the LLM call or JSON parse fails
- Returns the complete report dict (matching the `career_dna_reports` DB schema)

---

## `app/services/` — Business Logic

Services orchestrate: they call repositories to load data, call agents to process it, and call repositories again to save the result. They are the only layer allowed to combine multiple repositories or agents in one operation.

### `session_service.py`

| Function | What it does |
|----------|--------------|
| `start_session(user_id, domain, difficulty)` | Creates a new session ID, calls `create_initial_state()`, saves to DB, assembles the opening response (messages, voice memo, sprint board, hints). |
| `handle_action(session_id, user_action, current_user)` | Loads session, verifies ownership, runs the LangGraph director, saves updated state, returns the action response. |
| `get_session_state(session_id)` | Loads and returns the full session state dict. |
| `get_opening_messages(session_id)` | Loads the session and re-derives the opening messages from the scenario config. |
| `pause_session(session_id, current_user)` | Sets `session_status = "paused"` and saves. |
| `complete_session(session_id, current_user)` | Sets `session_status = "simulation_complete"` and saves. |

The director (`_director = build_director()`) is instantiated at module import time — once per process.

### `report_service.py`

`generate_report(user_id, session_ids)`:
1. Loads each session from the repository
2. Passes sessions to `career_fit_agent.generate_fit_report_data()`
3. Passes fit data to `report_agent.generate_report_narrative()`
4. Saves the report via `reports_repo.save_report()`
5. Returns the full response dict

---

## `app/api/v1/` — HTTP Route Handlers

The thinnest layer. Routers parse the HTTP request, call one service function, and return the result. No business logic. No direct database access.

### `sessions.py`

All session endpoints: `/session/start`, `/session/action`, `/session/{id}/state`, `/session/{id}/opening`, `/session/{id}/pause`, `/session/{id}/complete`, `/sessions/incomplete`.

The `/sessions/incomplete` endpoint is a direct repository call (no service needed — it's a straight DB query with no logic).

### `users.py`

`POST /user/onboarding` — validates Supabase is available, calls `users_repo.save_onboarding()`.

### `reports.py`

`POST /report/generate` — validates `session_ids` is non-empty, calls `report_service.generate_report()`.

---

## `tests/`

### `conftest.py`

Shared pytest fixtures:
- `test_director` — a LangGraph graph built with mock nodes instead of real LLM calls. Lets `test_director.py` test routing, state transitions, and scoring logic without a Groq API key.
- `initial_state` — a fresh `SimulationState` for the `pm` domain (pre-loaded scenario config).

### `test_director.py`

5 unit tests covering the director's routing and state behaviour:
1. Clarification message → routes to `npc_node` (no score)
2. Defer decision → routes to `score_node` → `npc_node`
3. Scene complete → routes to `scene_transition_node`
4. Blind accept → scores then transitions (no NPC)
5. State structure integrity after a scored interaction

Run with: `pytest tests/test_director.py` (no API key required)

### `test_pm_e2e.py`

8 integration tests against a live server. Automatically skipped if the server isn't running on port 8000.

Covers: health check, session start, opening endpoint, clarification routing, defer scoring, scene transition, state endpoint, report generation.

Run with: `pytest tests/test_pm_e2e.py` (requires server + Groq key)

---

## `scenarios/` — DO NOT MODIFY

JSON scenario files authored by Hassan. The director loads these at session start.

```
scenarios/
├── pm/
│   ├── scene_1.json … scene_4.json   ← scene configs, branch points, sprint boards
│   ├── sara_khan.json                ← NPC: personality, voice memo, opening messages
│   ├── rayan_ahmed.json              ← NPC
│   └── zara_malik.json               ← NPC
└── sqa/
    ├── sqa_scene_1.json … sqa_scene_4.json
    └── dan_frontend_dev.json
```

**Domains with no scenarios yet:** `data_analyst`, `frontend`, `backend` — starting a session for these domains will load empty config and run in a degraded state.

---

## `database/schema.sql`

Full Supabase/PostgreSQL schema. Run this in the Supabase SQL editor to set up a fresh project.

**Tables:** `users`, `user_profiles`, `sessions`, `stakeholder_trust`, `scores`, `decisions_log`, `npc_memory`, `career_dna_reports`

**Views:** `student_completed_domains`, `admin_session_overview`

**RLS:** Row-level security is enabled on all tables. Students see only their own data; admins see everything.

> Note: The `scores` table and `decisions_log` table are defined in the schema but are **not yet written to by the backend**. Scores and decisions are stored in the `scene_state` JSONB blob on the `sessions` table. The separate tables exist for future normalisation.
