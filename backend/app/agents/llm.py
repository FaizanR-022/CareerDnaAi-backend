from app.core.config import get_settings


def get_llm(model: str = "llama-3.3-70b-versatile", temperature: float = 0.3):
    """
    Provider abstraction. Set LLM_PROVIDER env var to switch.
    Supported: groq, openrouter
    """
    settings = get_settings()
    provider = settings.llm_provider

    if provider == "groq":
        from langchain_groq import ChatGroq
        return ChatGroq(
            model=model,
            temperature=temperature,
            api_key=settings.groq_api_key,
        )
    elif provider == "openrouter":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=model,
            temperature=temperature,
            openai_api_key=settings.openrouter_api_key,
            openai_api_base="https://openrouter.ai/api/v1",
        )
    else:
        raise ValueError(f"Unknown LLM_PROVIDER: {provider}. Use 'groq' or 'openrouter'.")
