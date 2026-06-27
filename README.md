# CareerDNA AI — Backend

FastAPI + LangGraph simulation director for the CareerDNA AI career simulator.

## Branch Structure

| Branch | Contents |
|--------|----------|
| `main` | **This branch** — FastAPI backend, LangGraph director, DB schema |
| `master` | Next.js 16 frontend |

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
```

> ⚠️ Never commit `.env` — it is in `.gitignore`.

## Running the API

```bash
cd backend
uvicorn api:app --reload --port 8000
```

API will be live at `http://localhost:8000`.

## Running Tests

```bash
cd backend
venv/bin/python tests/test_director.py
```

All 5 tests run without a real LLM key (uses mocks).

## Key Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/session/start` | Start a new simulation session |
| `POST` | `/session/action` | Submit a student action, get NPC response + score |
| `GET` | `/session/{id}/state` | Inspect full session state (debug) |