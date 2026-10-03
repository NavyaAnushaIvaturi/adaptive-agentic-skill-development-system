import os

from dotenv import load_dotenv


# Load environment variables from the .env file.
load_dotenv()


# Store application configuration and API keys.
class Settings:

    GROQ_API_KEY: str = os.getenv(
        "GROQ_API_KEY",
        "",
    )

    LANGSMITH_API_KEY: str = os.getenv(
        "LANGSMITH_API_KEY",
        "",
    )

    LANGCHAIN_TRACING_V2: str = os.getenv(
        "LANGCHAIN_TRACING_V2",
        "false",
    )

    LANGCHAIN_PROJECT: str = os.getenv(
        "LANGCHAIN_PROJECT",
        "adaptive-agentic-learning-system",
    )

    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite:///./learning.db",
    )

    TAVILY_API_KEY: str = os.getenv(
        "TAVILY_API_KEY",
        "",
    )


# Create one shared settings object for the application.
settings = Settings()