# CareerDNA AI — Backend

FastAPI backend for the CareerDNA AI career simulator. Students work through
AI-generated career simulation scenes one at a time; their responses are
evaluated, and a Career DNA Report is generated from the results.

## Branch Structure

| Branch | Contents |
|--------|----------|
| `main` | **This branch** — FastAPI backend, agent layer, DB schema |
| `master` | Next.js frontend |

---

## Architecture

- **Core backend** (`app/`, everything except `app/agents/`) owns the
  session/scene orchestration API, the database schema, and auth/user
  management. It never implements scene-generation, response-evaluation, or
  report-narrative logic itself — it calls into the agent layer through a
  fixed contract (`app/schemas/agent_contracts.py`) instead.
- **Agent layer** (`app/agents/`) is owned by the AI team — scene
  generation, response evaluation, and report narrative, all LLM-backed.
  Core backend dispatches to it via `app/services/agent_client.py`, which
  switches between a deterministic mock (`app/services/mock_agent.py`) and
  the real agent functions based on `AGENT_LAYER_IMPL` (`mock` by default —
  the whole API works end-to-end without any real LLM calls or agent-layer
  code being wired in yet).
- **Data access**: all Supabase calls go through `app/repositories/`
  (`supabase-py`, one file per table/concern) — never called directly from
  services or routers. The new-flow repositories additionally support a
  memory-only fallback for local dev without Supabase configured; a real
  Supabase failure (vs. "not configured") surfaces as a clean `503` rather
  than silently degrading.
- **Schema migrations** run through Alembic + SQLAlchemy Core (`alembic/`)
  — used only for versioning DDL, not as an ORM; the app's normal request
  path stays entirely on `supabase-py`.
- **API responses** are uniformly wrapped: `{"success": true, "data": ...}`
  on success, `{"success": false, "error": {"message", "status_code",
  "details"?}}` on any error (validation, known `HTTPException`s, or
  unexpected crashes) — handled centrally in `app/core/response_envelope.py`.
- **Auth** is fully custom (own JWTs via `PyJWT` + `bcrypt`), not Supabase
  Auth — the backend connects with the `service_role` key and enforces
  ownership checks in application code.

---

## Project Structure

```
backend/
├── app/
│   ├── main.py              # App factory: middleware, routers, /, /health
│   ├── core/                 # Settings, logging, JWT auth, response envelope
│   ├── db/                   # Supabase client singleton
│   ├── schemas/               # Pydantic request/response models + agent_contracts.py
│   ├── repositories/          # All Supabase access (one file per table/concern)
│   ├── services/               # Business logic + agent_client/mock_agent dispatch
│   ├── agents/                  # Agent layer (AI team's — do not edit): director,
│   │                             career_fit_agent, report_agent, llm
│   └── api/v1/                   # FastAPI route handlers (thin layer), mounted under /api/v1
├── alembic/                  # Schema migrations (Alembic + SQLAlchemy Core)
├── scenarios/                # JSON scenario content (Hassan's — do not edit)
├── database/                 # schema.sql — full current schema, reference only
└── tests/                    # pytest test suite
```

Request flow: **Router → Service → Repository**

---

## Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Environment Variables

Copy `.env.example` to `.env` and fill in your keys:

```bash
cp backend/.env.example backend/.env
```

```env
GROQ_API_KEY=...
OPENROUTER_API_KEY=...
LLM_PROVIDER=groq
SUPABASE_URL=...
# Must be the service_role key, not anon — backend enforces authorization itself.
SUPABASE_KEY=...
# Direct Postgres connection string, for Alembic migrations only — NOT used
# by the app's normal request path. Supabase: Project Settings -> Database
# -> Connection string -> "Session pooler" mode.
DATABASE_URL=postgresql://postgres.xxxxx:[PASSWORD]@aws-0-region.pooler.supabase.com:5432/postgres
FRONTEND_URL=https://careerdnaai.vercel.app
# Generate with: python -c "import secrets; print(secrets.token_urlsafe(48))"
JWT_SECRET_KEY=...
# "mock" (default) or "real" — switches the agent-layer dispatch.
AGENT_LAYER_IMPL=mock
```

> Never commit `.env` — it is in `.gitignore`. If `JWT_SECRET_KEY` is unset,
> auth falls back to a fixed dev user for local convenience — don't rely on
> this outside local dev.

---

## Running the API

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

API will be live at `http://localhost:8000`. Interactive docs at
`http://localhost:8000/docs` (shows the unwrapped response shapes —
the `{success, data}` envelope wraps them at the ASGI level, outside
what `response_model`/OpenAPI can describe).

> **Render dashboard:** ensure the start command is set to
> `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

---

## Database Migrations

Schema changes go through Alembic, not hand-edited SQL run directly against
Supabase:

```bash
cd backend
alembic upgrade head              # apply all pending migrations
alembic revision -m "description" # create a new empty migration
alembic current                   # show the currently-applied revision
```

`database/schema.sql` is kept only as a human-readable snapshot of the full
current schema — it is not the source of truth for applying changes.

---

## Running Tests

```bash
cd backend
pytest
```

Most of the suite runs as **real integration tests against the Supabase
project configured in `.env`** — not a mock database client. A shared
fixture creates a disposable test user per test (cascading delete cleans up
everything created against it), and skips cleanly (not a failure) if
Supabase isn't reachable. `test_director.py` (agent-owned) and a handful of
pure-logic files (schemas, security, mock agent, response envelope) don't
need a DB at all. Scene/evaluation generation uses the deterministic mock
agent by default — no real LLM key is required to run the suite.

---

## API

All routes are versioned under `/api/v1` (except `/` and `/health`).
Every response is wrapped:

```json
// success
{ "success": true, "data": { ... } }

// error
{ "success": false, "error": { "message": "...", "status_code": 404, "details"?: [...] } }
```

### Key Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET`  | `/health` | Health check + Supabase/LLM status (unversioned) |
| `POST` | `/api/v1/auth/signup` | Create an account, returns tokens |
| `POST` | `/api/v1/auth/signin` | Sign in, returns tokens |
| `POST` | `/api/v1/auth/refresh` | Rotate an access/refresh token pair |
| `POST` | `/api/v1/auth/logout` | Revoke a refresh token |
| `POST` | `/api/v1/user/onboarding` | Save onboarding profile data, returns 5 AI-generated calibration MCQs |
| `GET`  | `/api/v1/users/me` | Current user's profile |
| `PATCH`| `/api/v1/users/me` | Partial profile update |
| `GET`  / `DELETE` | `/api/v1/users/{user_id}` | Get / soft-delete a user (self or admin) |
| `POST` | `/api/v1/simulations` | Start a new simulation, returns scene 1 |
| `POST` | `/api/v1/simulations/{id}/scenes/{n}/responses` | Submit a response to scene `n`, returns evaluation |
| `POST` | `/api/v1/simulations/{id}/scenes` | Generate and return the next scene |
| `GET`  | `/api/v1/simulations/{id}/scenes/current` | Re-fetch the current scene (no generation) |
| `GET`  | `/api/v1/simulations/{id}` | Session status + per-scene progress |
| `GET`  | `/api/v1/simulations` | List the current user's simulation sessions |
| `POST` | `/api/v1/reports` | Generate a Career DNA Report from completed session IDs |
| `GET`  | `/api/v1/reports/{id}` / `/api/v1/reports` | Get one report / list the current user's reports |

---

## Team

| Person | Owns |
|--------|------|
| Faizan | Core backend — `app/` (except `app/agents/`), DB schema, admin API |
| Shayan, Ayesha | Agent layer — `app/agents/` (scene generation, response evaluation, report narrative), all LLM-backed |
| Ali | Frontend (`master` branch) |
| Hassan | Scenario content (`scenarios/`) |

> `app/agents/` and `scenarios/` are the AI team's — do not modify without
> their sign-off, even though core backend doesn't need to match their
> *current* internal shapes (they're mid-revamp; backend builds to its own
> contract, they adapt to it).
