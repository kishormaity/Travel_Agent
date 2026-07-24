from app.core.config import settings


def get_embeddings(
    provider: str | None = None,
    model_name: str | None = None,
):
    """
    Centralized Embeddings Factory for provider-agnostic text embeddings.
    Safely encapsulates provider-specific classes inside app/core/embeddings.py.
    """
    target_provider = (provider or settings.embedding_provider).lower()
    target_model = model_name or settings.embedding_model_name

    if target_provider == "openai":
        from langchain_openai import OpenAIEmbeddings

        kwargs = {}
        if settings.openai_api_key:
            kwargs["openai_api_key"] = settings.openai_api_key
        return OpenAIEmbeddings(model=target_model, **kwargs)

    raise ValueError(f"Unsupported embedding provider: '{target_provider}'")
