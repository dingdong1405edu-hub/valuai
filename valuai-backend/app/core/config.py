from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # App
    APP_ENV: str = "development"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    FRONTEND_URL: str = "http://localhost:3000"

    # Database — Railway PostgreSQL
    DATABASE_PUBLIC_URL: str = ""
    DATABASE_URL: str = ""

    # Groq
    GROQ_API_KEY: str
    GROQ_MODEL: str = "deepseek-r1-distill-llama-70b"        # upgraded: better reasoning
    GROQ_EXTRACTION_MODEL: str = "llama-3.3-70b-versatile"   # reliable JSON extraction

    # Google AI
    GOOGLE_API_KEY: str
    GEMINI_MODEL: str = "gemini-2.5-flash"                   # upgraded from 2.0
    EMBEDDING_MODEL: str = "models/gemini-embedding-001"

    # Optional external APIs
    FIRECRAWL_API_KEY: Optional[str] = None
    FIREANT_TOKEN: Optional[str] = None
    FIREANT_BASE_URL: str = "https://restv2.fireant.vn"

    @property
    def async_db_url(self) -> str:
        """Convert postgresql:// → postgresql+asyncpg:// for SQLAlchemy async engine."""
        url = self.DATABASE_PUBLIC_URL or self.DATABASE_URL
        if not url:
            raise ValueError("DATABASE_PUBLIC_URL or DATABASE_URL must be set")
        if url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url

    @property
    def is_dev(self) -> bool:
        return self.APP_ENV == "development"


settings = Settings()
