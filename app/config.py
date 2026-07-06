from dotenv import load_dotenv
import os

# Load environment variables from .env
load_dotenv()

# ==========================
# API Keys
# ==========================
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

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
    raise ValueError(
        "GROQ_API_KEY is not set. Please add it to your .env file."
    )