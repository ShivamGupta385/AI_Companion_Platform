from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict
)


class Settings(BaseSettings):
    DATABASE_URL: str

    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    OPENAI_API_KEY: str

    ELEVENLABS_API_KEY: str
    VOICE_ID: str

    PINECONE_API_KEY: str
    PINECONE_INDEX_NAME: str

    LIVEAVATAR_API_KEY: str
    LIVEAVATAR_AVATAR_ID: str

    HEYGEN_API_KEY: str
    HEYGEN_AVATAR_ID: str

    TAVUS_API_KEY: str
    TAVUS_BASE_URL: str
    TAVUS_REPLICA_ID: str
    TAVUS_PERSONA_ID: str

    LIVEAVATAR_SECRET_ID: str
    ELEVENLABS_AGENT_ID: str

    # ---------------------------------
    # Tavus Callback URL
    # ---------------------------------
    BACKEND_URL: str = "http://localhost:8000"  # ⬅️ ADD THIS LINE

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )


settings = Settings()