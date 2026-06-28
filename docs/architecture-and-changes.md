# CareerDNA AI — Architecture & Changes

**Project:** CareerDNA AI Backend  
**Refactor author:** Faizan  
**Date:** June 2026  

---

## 1. What Changed and Why

The backend was initially delivered as a single `api.py` file (464 lines) that mixed HTTP routing, database access, authentication, business logic, and agent orchestration with no separation of concerns. This made the codebase hard to read, hard to test, and difficult for multiple teammates to work on simultaneously.

The goal of this refactor was to restructure it into a production-grade layered architecture without changing any existing API contracts, response shapes, or observable behavior.

---

## 2. Before vs. After

### Before

```
backend/
├── api.py              ← everything in one file
├── agents/
│   ├── director.py     ← LangGraph graph + LLM factory
│   ├── career_fit_agent.py
│   └── report_agent.py ← imported get_llm from director (tight coupling)
├── tests/
│   ├── test_director.py   ← standalone script, not pytest-compatible
│   └── test_pm_e2e.py     ← standalone script
├── scenarios/
└── requirements.txt    ← no version pins
```

**Problems with the old structure:**
- `api.py` owned Supabase client init, auth, session persistence, 8 route handlers, request schemas, and report orchestration — all in 464 lines
- `report_agent.py` imported `get_llm()` from `agents/director.py`, coupling two unrelated agents
- All logging was `print()` statements with no timestamps or levels
- `requirements.txt` had zero version pins — LangGraph and LangChain break frequently across minor versions
- Tests were standalone scripts run with `python test_director.py`, not discoverable by pytest
- No `__init__.py` files; tests hacked `sys.path` to find imports

### After

```
backend/
├── app/
│   ├── core/           ← settings, logging, auth (cross-cutting concerns)
│   ├── db/             ← Supabase client singleton
│   ├── schemas/        ← Pydantic request/response contracts
│   ├── repositories/   ← ALL Supabase access (one file per table)
│   ├── services/       ← business logic
│   ├── agents/         ← LangGraph graph + agents
│   └── api/v1/         ← thin HTTP route handlers
├── main.py
├── tests/              ← pytest-compatible
├── scenarios/          ← untouched
├── requirements.txt    ← pinned versions
└── requirements-dev.txt
```

---

## 3. Layered Architecture

The backend follows a strict three-layer request flow:

```
HTTP Request
     │
     ▼
┌─────────────────┐
│   api/v1/       │  Parse HTTP, call service, return result.
│  (Router layer) │  No business logic. No DB access.
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   services/     │  Orchestrate: load session, invoke director,
│ (Service layer) │  build response. Owns business rules.
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  repositories/  │  ALL Supabase calls live here.
│  (Data layer)   │  Routers and services never touch Supabase directly.
└─────────────────┘
```

Agents sit outside this flow — they are called by services, not by repositories or routers.

---

## 4. File-by-File Change Summary

| File | Status | What changed |
|------|--------|--------------|
| `api.py` | **Deleted** | Split into routers + services + repositories + core |
| `agents/director.py` | **Moved + updated** | Now at `app/agents/director.py`. Imports `get_llm` from `app/agents/llm.py`. Uses `logging` instead of `print()`. Path resolution updated (3 parent levels instead of 2). File handles fixed with `with open()`. |
| `agents/career_fit_agent.py` | **Moved** | Now at `app/agents/career_fit_agent.py`. No logic changes. |
| `agents/report_agent.py` | **Moved + updated** | Now at `app/agents/report_agent.py`. Imports `get_llm` from `app/agents/llm.py` instead of `agents/director.py`. |
| *(new)* `app/agents/llm.py` | **New** | `get_llm()` factory extracted from `director.py`. Single source of truth for LLM provider selection. |
| *(new)* `app/core/config.py` | **New** | `pydantic-settings` Settings class. Replaces all `os.getenv()` calls scattered across the codebase. |
| *(new)* `app/core/logging.py` | **New** | Centralised `logging.basicConfig()` setup. All modules now use `logging.getLogger(__name__)`. |
| *(new)* `app/core/auth.py` | **New** | `get_current_user()` FastAPI dependency extracted from `api.py`. |
| *(new)* `app/db/client.py` | **New** | Supabase client singleton. `init_supabase()` called once at startup. `get_supabase()` used everywhere else. |
| *(new)* `app/schemas/` | **New** | Pydantic models extracted from `api.py` into separate files per domain. |
| *(new)* `app/repositories/sessions.py` | **New** | `save_session()`, `load_session()`, `get_incomplete_sessions()` extracted from `api.py`. |
| *(new)* `app/repositories/users.py` | **New** | Onboarding DB writes extracted from `api.py`. |
| *(new)* `app/repositories/reports.py` | **New** | `save_report_to_supabase()` extracted from `report_agent.py`. |
| *(new)* `app/services/session_service.py` | **New** | All session business logic from `api.py` route handlers. |
| *(new)* `app/services/report_service.py` | **New** | Report generation pipeline from `api.py` `/report/generate` handler. |
| *(new)* `app/api/v1/sessions.py` | **New** | Thin session route handlers. |
| *(new)* `app/api/v1/users.py` | **New** | Thin user route handler. |
| *(new)* `app/api/v1/reports.py` | **New** | Thin report route handler. |
| *(new)* `app/main.py` | **New** | App factory: creates FastAPI instance, registers middleware, includes routers. |
| `tests/test_director.py` | **Rewritten** | Converted from standalone script to pytest functions. Same 5 assertions, same mock nodes. |
| `tests/test_pm_e2e.py` | **Rewritten** | Converted to pytest. Auto-skips if server not running on `:8000`. |
| *(new)* `tests/conftest.py` | **New** | Shared fixtures: `test_director` (mock graph), `initial_state`. |
| `requirements.txt` | **Updated** | All dependencies now pinned to exact versions. `pydantic-settings` added. |
| *(new)* `requirements-dev.txt` | **New** | Test-only deps (`pytest`, `httpx`) separated from production deps. |
| *(new)* `pytest.ini` | **New** | Configures `testpaths = tests` and `pythonpath = .`. |
| `.gitignore` | **Updated** | Added `.pytest_cache/`, `.coverage`, `htmlcov/`, `dist/`, `*.egg-info/`. |
| `README.md` | **Updated** | Reflects new entry point, test command, and project structure. |

---

## 5. API Contracts — Unchanged

Every existing API endpoint path, HTTP method, request shape, and response shape is identical to the pre-refactor version. The frontend and any teammate integrations require zero changes.

| Endpoint | Path unchanged | Request unchanged | Response unchanged |
|----------|---------------|-------------------|-------------------|
| `POST /session/start` | ✓ | ✓ | ✓ |
| `POST /session/action` | ✓ | ✓ | ✓ |
| `GET /session/{id}/state` | ✓ | ✓ | ✓ |
| `GET /session/{id}/opening` | ✓ | ✓ | ✓ |
| `POST /session/{id}/pause` | ✓ | ✓ | ✓ |
| `POST /session/{id}/complete` | ✓ | ✓ | ✓ |
| `GET /sessions/incomplete` | ✓ | ✓ | ✓ |
| `POST /user/onboarding` | ✓ | ✓ | ✓ |
| `POST /report/generate` | ✓ | ✓ | ✓ |

---

## 6. Known Issues (Documented, Not Fixed)

These were pre-existing behaviors that the rest of the team may rely on. They are preserved exactly as-is and flagged for team discussion.

| # | Location | Issue | Impact |
|---|----------|-------|--------|
| 1 | `repositories/sessions.py` | `last_active_at: "now()"` passes a SQL expression literal as a string. Supabase Python client doesn't evaluate it — the column stores the literal string `"now()"` instead of the actual timestamp. | `last_active_at` column is always wrong in Supabase. |
| 2 | `services/session_service.py` | `"npc_name": "Sara Khan"` is hardcoded in the `/session/action` response regardless of which NPC is actually active in the scene. | Multi-NPC scenes will report the wrong NPC name to the frontend. |
| 3 | `agents/director.py` | `branch_decision_accept_blindly` routes directly to `scene_transition_node`, skipping `npc_node`. The user gets no NPC reply when they blindly accept. | May be intentional (penalising blind accepts) or an oversight. Needs team confirmation. |
| 4 | `repositories/sessions.py` | If Supabase is connected but throws on save/load, the code silently falls back to the in-memory dict (which is empty on a restarted server). Sessions can silently disappear. No 500 is surfaced to the caller. | Potential silent data loss in production if Supabase has transient errors. |

---

## 7. Deployment Checklist

- [ ] `pip install -r requirements.txt` on the Render instance (or let Render auto-install on deploy)
- [ ] **Update Render start command** to `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- [ ] Confirm all env vars set in Render: `GROQ_API_KEY`, `SUPABASE_URL`, `SUPABASE_KEY`, `FRONTEND_URL`, `LLM_PROVIDER`
- [ ] Run `pytest tests/test_director.py` locally to confirm all 5 unit tests pass (no API key needed)
- [ ] Run the e2e test against staging before hitting production
