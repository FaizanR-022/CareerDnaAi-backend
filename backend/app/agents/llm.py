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

import time

def call_llm_with_retry(llm, messages, stop=None, max_retries=3):
    """
    Calls LLM with exponential backoff on rate limit errors.
    Waits: 2s, 4s, 8s between retries.
    Falls through after max_retries so caller can handle fallback.
    """
    for attempt in range(max_retries):
        try:
            if stop:
                return llm.invoke(messages, stop=stop)
            return llm.invoke(messages)
        except Exception as e:
            error_str = str(e).lower()
            if ("429" in error_str or "rate limit" in error_str or "too many requests" in error_str):
                if attempt < max_retries - 1:
                    wait_seconds = 2 ** (attempt + 1)  # 2, 4, 8
                    import logging
                    logging.getLogger(__name__).warning(
                        f"Groq rate limit hit (attempt {attempt+1}/{max_retries}). "
                        f"Waiting {wait_seconds}s before retry."
                    )
                    time.sleep(wait_seconds)
                    continue
            raise  # re-raise non-rate-limit errors immediately
    raise Exception("Max retries exceeded for LLM call")


import asyncio

async def acall_llm_with_retry(llm, messages, stop=None, max_retries=3):
    """
    Async version of call_llm_with_retry.
    Uses ainvoke() to avoid blocking FastAPI worker threads.
    """
    for attempt in range(max_retries):
        try:
            if stop:
                return await llm.ainvoke(messages, stop=stop)
            return await llm.ainvoke(messages)
        except Exception as e:
            error_str = str(e).lower()
            if ("429" in error_str or "rate limit" in error_str or
                    "too many requests" in error_str):
                if attempt < max_retries - 1:
                    wait_seconds = 2 ** (attempt + 1)
                    import logging
                    logging.getLogger(__name__).warning(
                        f"Groq rate limit hit async (attempt {attempt+1}/{max_retries}). "
                        f"Waiting {wait_seconds}s."
                    )
                    await asyncio.sleep(wait_seconds)
                    continue
            raise
    raise Exception("Max retries exceeded for async LLM call")
