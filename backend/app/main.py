import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import reports, sessions, users
from app.core.config import get_settings
from app.core.logging import setup_logging
from app.db.client import get_supabase, init_supabase

setup_logging()
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    settings = get_settings()
    init_supabase()

    app = FastAPI(title="Career Simulator — Director API", version="2.0")

    allowed_origins = [o for o in [
        "http://localhost:3000",
        "https://careerdnaai.vercel.app",
        settings.frontend_url,
    ] if o]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(sessions.router)
    app.include_router(users.router)
    app.include_router(reports.router)

    @app.get("/")
    def root():
        return {"status": "Career Simulator API running", "version": "2.0"}

    @app.get("/health")
    def health():
        return {
            "status": "ok",
            "supabase": "connected" if get_supabase() else "memory-only mode",
            "llm_provider": settings.llm_provider,
        }

    return app


app = create_app()
