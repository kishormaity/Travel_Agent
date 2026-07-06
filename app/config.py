from dotenv import load_dotenv
import os

load_dotenv()

# ==========================
# API Keys
# ==========================

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
GEOAPIFY_API_KEY = os.getenv("GEOAPIFY_API_KEY")

if not GEOAPIFY_API_KEY:
    raise ValueError("GEOAPIFY_API_KEY is missing.")

AVIATIONSTACK_API_KEY = os.getenv("AVIATIONSTACK_API_KEY")

if not AVIATIONSTACK_API_KEY:
    raise ValueError("AVIATIONSTACK_API_KEY is missing.")


WEATHER_API_BASE_URL = os.getenv(
    "WEATHER_API_BASE_URL",
    "https://api.weatherapi.com/v1"
)


CURRENCY_API_BASE_URL = os.getenv(
    "CURRENCY_API_BASE_URL",
    "https://api.frankfurter.dev/v1"
)

GEOAPIFY_API_BASE_URL = os.getenv(
    "GEOAPIFY_API_BASE_URL",
    "https://api.geoapify.com/v2/places"
)

AVIATIONSTACK_API_BASE_URL = os.getenv(
    "AVIATIONSTACK_API_BASE_URL",
    "http://api.aviationstack.com/v1"
)

GEOAPIFY_ROUTING_API_BASE_URL = os.getenv(
    "GEOAPIFY_ROUTING_API_BASE_URL",
    "https://api.geoapify.com/v1/routing"
)

# ==========================
# LLM Configuration
# ==========================

MODEL_NAME = os.getenv("MODEL_NAME", "llama-3.3-70b-versatile")
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "1024"))

# ==========================
# Validation
# ==========================

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY not found in .env")

if not WEATHER_API_KEY:
    raise ValueError("WEATHER_API_KEY not found in .env")