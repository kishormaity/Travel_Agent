from groq import Groq
from app.config import GROQ_API_KEY

def get_llm() -> Groq:
    """
    Initialize and return the Groq LLM client.
    """
    return Groq(api_key=GROQ_API_KEY)
