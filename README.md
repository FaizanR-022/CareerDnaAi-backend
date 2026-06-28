# CareerDNA AI — Backend

FastAPI + LangGraph simulation director for the CareerDNA AI career simulator.

## Branch Structure

| Branch | Contents |
|--------|----------|
| `main` | **This branch** — FastAPI backend, LangGraph director, DB schema |
| `master` | Next.js frontend |

---

## Project Structure

```
backend/
├── app/
│   ├── core/           # Settings, logging, JWT auth
│   ├── db/             # Supabase client singleton
│   ├── schemas/        # Pydantic request/response models
│   ├── repositories/   # All Supabase access (one file per table)
│   ├── services/       # Business logic
│   ├── agents/         # LangGraph director + career fit + report agents
│   └── api/v1/         # FastAPI route handlers (thin layer)
├── main.py             # App factory + middleware
├── scenarios/          # JSON scenario content (Hassan's — do not edit)
├── database/           # schema.sql
└── tests/              # pytest test suite
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
SUPABASE_KEY=...
FRONTEND_URL=https://careerdnaai.vercel.app
```

> Never commit `.env` — it is in `.gitignore`.

---

## Running the API

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

API will be live at `http://localhost:8000`.
Interactive docs at `http://localhost:8000/docs`.

> **Render dashboard:** ensure the start command is set to
> `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

---

## Running Tests

```bash
cd backend
pytest tests/
```

`tests/test_director.py` runs without a real LLM key (uses mock nodes).
`tests/test_pm_e2e.py` requires the server running on port 8000 and a live Groq key — it auto-skips if the server is not reachable.

---

## Key Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET`  | `/health` | Health check + Supabase/LLM status |
| `POST` | `/session/start` | Start a new simulation session |
| `POST` | `/session/action` | Submit a student action, get NPC response + score |
| `GET`  | `/session/{id}/state` | Full session state (resume / admin view) |
| `GET`  | `/session/{id}/opening` | Opening messages + voice memo for a session |
| `POST` | `/session/{id}/pause` | Save & exit |
| `POST` | `/session/{id}/complete` | Mark session complete |
| `GET`  | `/sessions/incomplete` | List active/paused sessions for current user |
| `POST` | `/user/onboarding` | Save onboarding data |
| `POST` | `/report/generate` | Generate Career DNA Report from session IDs |

Full request/response documentation: `docs/api-reference.md`

---

## Team

| Person | Owns |
|--------|------|
| Faizan | Backend (`app/`, `tests/`) |
| Ali / Shayan | Frontend (master branch) |
| Hassan | Scenario content (`scenarios/`) |
| Ayesha | Report narrative (`app/agents/report_agent.py`) |

> `scenarios/` is Hassan's content — do not modify.
