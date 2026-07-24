import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()


class Settings(BaseModel):
    """
    Centralized, strongly-typed application settings.
    """

    # Model & Provider Configuration
    model_provider: str = Field(
        default_factory=lambda: os.getenv("LLM_PROVIDER", os.getenv("MODEL_PROVIDER", "groq"))
    )
    model_name: str = Field(
        default_factory=lambda: os.getenv("MODEL_NAME", "llama-3.3-70b-versatile")
    )
    embedding_provider: str = Field(
        default_factory=lambda: os.getenv("EMBEDDING_PROVIDER", "openai")
    )
    embedding_model_name: str = Field(
        default_factory=lambda: os.getenv("EMBEDDING_MODEL_NAME", "text-embedding-3-small")
    )

    # LLM Hyperparameters
    temperature: float = Field(
        default_factory=lambda: float(os.getenv("TEMPERATURE", "0.7"))
    )
    planner_temperature: float = Field(
        default_factory=lambda: float(os.getenv("PLANNER_TEMPERATURE", "0.0"))
    )
    response_temperature: float = Field(
        default_factory=lambda: float(os.getenv("RESPONSE_TEMPERATURE", "0.7"))
    )
    max_tokens: int = Field(
        default_factory=lambda: int(os.getenv("MAX_TOKENS", "1024"))
    )

    # API Keys
    groq_api_key: str | None = Field(
        default_factory=lambda: os.getenv("GROQ_API_KEY")
    )
    openai_api_key: str | None = Field(
        default_factory=lambda: os.getenv("OPENAI_API_KEY")
    )
    weather_api_key: str | None = Field(
        default_factory=lambda: os.getenv("WEATHER_API_KEY")
    )
    geoapify_api_key: str | None = Field(
        default_factory=lambda: os.getenv("GEOAPIFY_API_KEY")
    )
    aviationstack_api_key: str | None = Field(
        default_factory=lambda: os.getenv("AVIATIONSTACK_API_KEY")
    )

    # Service Base URLs
    weather_api_base_url: str = Field(
        default_factory=lambda: os.getenv("WEATHER_API_BASE_URL", "https://api.weatherapi.com/v1")
    )
    currency_api_base_url: str = Field(
        default_factory=lambda: os.getenv("CURRENCY_API_BASE_URL", "https://api.frankfurter.dev/v1")
    )
    geoapify_api_base_url: str = Field(
        default_factory=lambda: os.getenv("GEOAPIFY_API_BASE_URL", "https://api.geoapify.com/v2/places")
    )
    aviationstack_api_base_url: str = Field(
        default_factory=lambda: os.getenv("AVIATIONSTACK_API_BASE_URL", "http://api.aviationstack.com/v1")
    )
    geoapify_routing_api_base_url: str = Field(
        default_factory=lambda: os.getenv("GEOAPIFY_ROUTING_API_BASE_URL", "https://api.geoapify.com/v1/routing")
    )

    def validate_keys(self) -> None:
        """Validate critical external service keys."""
        if self.model_provider == "groq" and not self.groq_api_key:
            raise ValueError("GROQ_API_KEY not found in environment for LLM_PROVIDER='groq'")
        if self.model_provider == "openai" and not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY not found in environment for LLM_PROVIDER='openai'")
        if not self.weather_api_key:
            raise ValueError("WEATHER_API_KEY not found in environment.")
        if not self.geoapify_api_key:
            raise ValueError("GEOAPIFY_API_KEY not found in environment.")
        if not self.aviationstack_api_key:
            raise ValueError("AVIATIONSTACK_API_KEY not found in environment.")


settings = Settings()

# Backwards compatibility top-level module exports
GROQ_API_KEY = settings.groq_api_key
OPENAI_API_KEY = settings.openai_api_key
WEATHER_API_KEY = settings.weather_api_key
GEOAPIFY_API_KEY = settings.geoapify_api_key
AVIATIONSTACK_API_KEY = settings.aviationstack_api_key

WEATHER_API_BASE_URL = settings.weather_api_base_url
CURRENCY_API_BASE_URL = settings.currency_api_base_url
GEOAPIFY_API_BASE_URL = settings.geoapify_api_base_url
AVIATIONSTACK_API_BASE_URL = settings.aviationstack_api_base_url
GEOAPIFY_ROUTING_API_BASE_URL = settings.geoapify_routing_api_base_url

MODEL_PROVIDER = settings.model_provider
MODEL_NAME = settings.model_name
TEMPERATURE = settings.temperature
PLANNER_TEMPERATURE = settings.planner_temperature
RESPONSE_TEMPERATURE = settings.response_temperature
MAX_TOKENS = settings.max_tokens
