from dotenv import load_dotenv
from langchain_groq import ChatGroq

from backend.config import settings


# Load environment variables from the .env file.
load_dotenv()


# Create and return the configured Groq language model.
def get_llm() -> ChatGroq:

    if not settings.GROQ_API_KEY:
        raise RuntimeError(
            "GROQ_API_KEY is not configured."
        )

    return ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0,
        api_key=settings.GROQ_API_KEY,
    )