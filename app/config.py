"""Application settings, read from environment variables / .env file."""
import os
from dataclasses import dataclass

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:  # python-dotenv is optional
    pass


@dataclass(frozen=True)
class Settings:
    anthropic_api_key: str = ""
    llm_model: str = "claude-haiku-5-5"
    database_path: str = "emails.db"
    review_threshold: float = 0.45

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", ""),
            llm_model=os.getenv("LLM_MODEL", "claude-haiku-5-5"),
            database_path=os.getenv("DATABASE_PATH", "emails.db"),
            review_threshold=float(os.getenv("REVIEW_CONFIDENCE_THRESHOLD", "0.45")),
        )
