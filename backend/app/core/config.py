from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict
)

from typing import Optional

class Settings(BaseSettings):
    DATABASE_URL: str

    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    OPENAI_API_KEY: Optional[str] = None

    PINECONE_API_KEY: str
    PINECONE_INDEX_NAME: str

    TAVUS_API_KEY: str
    TAVUS_BASE_URL: str
    TAVUS_WEBHOOK_URL: Optional[str] = None

    # ---------------------------------
    # Tavus Callback URL
    # ---------------------------------
    BACKEND_URL: str = "http://localhost:8000"  # ⬅️ ADD THIS LINE

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )


settings = Settings()