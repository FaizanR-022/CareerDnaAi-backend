from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    supabase_url: str = ""
    supabase_key: str = ""
    # Direct Postgres connection string — used only by Alembic migrations.
    # The app's normal request path never touches this; it stays on
    # supabase-py + supabase_url/supabase_key everywhere else.
    database_url: str = ""
    frontend_url: str = ""
    llm_provider: str = "groq"
    groq_api_key: str = ""
    groq_api_keys: str = ""
    openrouter_api_key: str = ""

    agent_layer_impl: Literal["mock", "real"] = "mock"

    jwt_secret_key: str = ""
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440  # 24h — refresh token handles longer sessions
    refresh_token_expire_days: int = 30

    model_config = {"env_file": ".env", "case_sensitive": False}

    @property
    def get_groq_api_keys(self) -> list[str]:
        keys = []
        if self.groq_api_keys:
            keys = [k.strip() for k in self.groq_api_keys.split(",") if k.strip()]
        if not keys and self.groq_api_key:
            keys = [self.groq_api_key.strip()]
        return keys


@lru_cache
def get_settings() -> Settings:
    return Settings()
