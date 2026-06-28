from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    supabase_url: str = ""
    supabase_key: str = ""
    frontend_url: str = ""
    llm_provider: str = "groq"
    groq_api_key: str = ""
    openrouter_api_key: str = ""

    model_config = {"env_file": ".env", "case_sensitive": False}


@lru_cache
def get_settings() -> Settings:
    return Settings()
