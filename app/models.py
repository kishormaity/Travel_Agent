from groq import Groq

from app.config import GROQ_API_KEY


def get_llm():
    """
    Initialize and return the Groq client.
    """
    return Groq(api_key=GROQ_API_KEY)