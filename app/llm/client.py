from langchain.chat_models import init_chat_model
from app.config import GROQ_API_KEY, MODEL_NAME

FALLBACK_MODELS = ["llama-3.1-8b-instant", "gemma2-9b-it"]


def get_llm(temperature: float = 0.0, model_name: str | None = None):
    """
    Initialize and return a native LangChain chat model with automatic fallback models for Groq rate limits.
    """
    target_model = model_name or MODEL_NAME
    primary_model = init_chat_model(
        target_model,
        model_provider="groq",
        groq_api_key=GROQ_API_KEY,
        temperature=temperature,
    )

    fallbacks = [
        init_chat_model(
            fb_model,
            model_provider="groq",
            groq_api_key=GROQ_API_KEY,
            temperature=temperature,
        )
        for fb_model in FALLBACK_MODELS
        if fb_model != target_model
    ]

    return primary_model.with_fallbacks(fallbacks, exceptions_to_handle=(Exception,))
