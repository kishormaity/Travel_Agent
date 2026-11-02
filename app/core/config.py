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
        default_factory=lambda: os.getenv("MODEL_NAME", "qwen/qwen3.8-27b")
    )
    groq_fallback_models: list[str] = Field(
        default_factory=lambda: [
            m.strip()
            for m in os.getenv(
                "GROQ_FALLBACK_MODELS", "openai/gpt-oss-120b,openai/gpt-oss-20b"
            ).split(",")
            if m.strip()
        ]
    )
    embedding_provider: str = Field(
        default_factory=lambda: os.getenv("EMBEDDING_PROVIDER", "fastembed")
    )
    embedding_model_name: str = Field(
        default_factory=lambda: os.getenv("EMBEDDING_MODEL_NAME", "BAAI/bge-small-en-v1.5")
    )
    embedding_dimension: int = Field(
        default_factory=lambda: int(os.getenv("EMBEDDING_DIMENSION", "384"))
    )

    # Qdrant Vector Database Configuration
    qdrant_url: str = Field(
        default_factory=lambda: os.getenv("QDRANT_URL", "http://localhost:6333")
    )
    qdrant_api_key: str | None = Field(
        default_factory=lambda: os.getenv("QDRANT_API_KEY")
    )
    qdrant_grpc_port: int = Field(
        default_factory=lambda: int(os.getenv("QDRANT_GRPC_PORT", "6334"))
    )
    qdrant_prefer_grpc: bool = Field(
        default_factory=lambda: os.getenv("QDRANT_PREFER_GRPC", "false").lower() == "true"
    )
    qdrant_timeout: float = Field(
        default_factory=lambda: float(os.getenv("QDRANT_TIMEOUT", "10.0"))
    )
    qdrant_location: str | None = Field(
        default_factory=lambda: os.getenv("QDRANT_LOCATION")
    )
    enable_hybrid_search: bool = Field(
        default_factory=lambda: os.getenv("ENABLE_HYBRID_SEARCH", "true").lower() == "true"
    )

    # Remote Hosted MCP Servers Configuration
    remote_mcp_enabled: bool = Field(
        default_factory=lambda: os.getenv("REMOTE_MCP_ENABLED", "true").lower() == "true"
    )
    maqami_mcp_url: str = Field(
        default_factory=lambda: os.getenv("MAQAMI_MCP_URL", "https://mcp.maqami.co/")
    )
    maqami_mcp_api_key: str | None = Field(
        default_factory=lambda: os.getenv("MAQAMI_MCP_API_KEY")
    )
    ticketlens_mcp_url: str = Field(
        default_factory=lambda: os.getenv("TICKETLENS_MCP_URL", "https://mcp.ticketlens.com/")
    )
    ticketlens_mcp_api_key: str | None = Field(
        default_factory=lambda: os.getenv("TICKETLENS_MCP_API_KEY")
    )
    octotrip_mcp_url: str = Field(
        default_factory=lambda: os.getenv("OCTOTRIP_MCP_URL", "https://mcp.octotrip.app/flights/mcp")
    )
    obo_mcp_url: str = Field(
        default_factory=lambda: os.getenv("OBO_MCP_URL", "https://onebookingonline.com/mcp")
    )
    obo_api_key: str | None = Field(
        default_factory=lambda: os.getenv("OBO_API_KEY")
    )
    hasdata_mcp_url: str = Field(
        default_factory=lambda: os.getenv("HASDATA_MCP_URL", "https://mcp.hasdata.com/mcp")
    )
    hasdata_api_key: str | None = Field(
        default_factory=lambda: os.getenv("HAS_DATA_API_KEY") or os.getenv("HASDATA_API_KEY")
    )
    remote_mcp_timeout: float = Field(
        default_factory=lambda: float(os.getenv("REMOTE_MCP_TIMEOUT", "75.0"))
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
    google_api_key: str | None = Field(
        default_factory=lambda: os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    )
    gemini_model_name: str = Field(
        default_factory=lambda: os.getenv("GEMINI_MODEL_NAME", "gemini-2.5-flash")
    )
    weather_api_key: str | None = Field(
        default_factory=lambda: os.getenv("WEATHER_API_KEY")
    )
    geoapify_api_key: str | None = Field(
        default_factory=lambda: os.getenv("GEOAPIFY_API_KEY")
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


settings = Settings()

# Backwards compatibility top-level module exports
GROQ_API_KEY = settings.groq_api_key
OPENAI_API_KEY = settings.openai_api_key
WEATHER_API_KEY = settings.weather_api_key
GEOAPIFY_API_KEY = settings.geoapify_api_key

WEATHER_API_BASE_URL = settings.weather_api_base_url
CURRENCY_API_BASE_URL = settings.currency_api_base_url
GEOAPIFY_API_BASE_URL = settings.geoapify_api_base_url
GEOAPIFY_ROUTING_API_BASE_URL = settings.geoapify_routing_api_base_url

MODEL_PROVIDER = settings.model_provider
MODEL_NAME = settings.model_name
GROQ_FALLBACK_MODELS = settings.groq_fallback_models
GEMINI_MODEL_NAME = settings.gemini_model_name
TEMPERATURE = settings.temperature
PLANNER_TEMPERATURE = settings.planner_temperature
RESPONSE_TEMPERATURE = settings.response_temperature
MAX_TOKENS = settings.max_tokens
