import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "SmartInsight"
    PROJECT_VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"

    # Database Settings
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/smartinsight_db",
    )
    
    # Redis Settings
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    CACHE_EXPIRATION_SECONDS: int = 3600

    # AI / LLM Settings
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    EMBEDDING_DIMENSION: int = 1536
    MOCK_LLM_IF_NO_KEY: bool = True

    # PDF & Chunking Settings
    CHUNK_SIZE: int = 600
    CHUNK_OVERLAP: int = 120
    TOP_K_CHUNKS: int = 4
    SIMILARITY_THRESHOLD: float = 0.25

    # Target TTFT benchmark (ms)
    TARGET_TTFT_MS: int = 350

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
