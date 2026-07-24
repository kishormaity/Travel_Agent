from langchain.chat_models import init_chat_model
from app.core.config import settings

FALLBACK_MODELS = ["llama-3.1-8b-instant", "gemma2-9b-it"]


def get_llm(
    temperature: float = 0.0,
    model_name: str | None = None,
    model_provider: str | None = None,
):
    """
    Standard Provider-Agnostic LLM Factory using LangChain's universal init_chat_model.
    Supports OpenAI, Groq, Anthropic, Gemini, Mistral, Ollama with ZERO code changes.
    """
    provider = model_provider or settings.model_provider
    model = model_name or settings.model_name

    kwargs = {}
    if provider == "groq" and settings.groq_api_key:
        kwargs["groq_api_key"] = settings.groq_api_key
    elif provider == "openai" and settings.openai_api_key:
        kwargs["openai_api_key"] = settings.openai_api_key

    primary_model = init_chat_model(
        model,
        model_provider=provider,
        temperature=temperature,
        **kwargs,
    )

    if provider == "groq":
        fallbacks = [
            init_chat_model(
                fb_model,
                model_provider=provider,
                temperature=temperature,
                **kwargs,
            )
            for fb_model in FALLBACK_MODELS
            if fb_model != model
        ]
        return primary_model.with_fallbacks(
            fallbacks,
            exceptions_to_handle=(Exception,),
        )

    return primary_model


def get_llm_with_tools(
    temperature: float = 0.0,
    model_name: str | None = None,
    model_provider: str | None = None,
):
    """
    Universal tool binding via standard LangChain .bind_tools().
    Works seamlessly across OpenAI, Groq, Anthropic, Google Gemini, etc.
    """
    from app.registry.tool_registry import LANGCHAIN_TOOLS

    return get_llm(
        temperature=temperature,
        model_name=model_name,
        model_provider=model_provider,
    ).bind_tools(LANGCHAIN_TOOLS)
