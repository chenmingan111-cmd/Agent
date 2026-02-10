import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    APP_ENV: str = "dev"
    APP_PORT: int = 8080

    ES_URL: str = "http://localhost:9200"
    ES_USER: str = "elastic"
    ES_PASSWORD: str = "changeme"
    ES_DEFAULT_INDEX: str = "orders-*"

    LLM_PROVIDER: str = "openai"
    LLM_MODEL: str = "gpt-4o"
    LLM_API_KEY: str

    MAX_VALIDATE_RETRY: int = 2
    MAX_SIZE: int = 200
    MAX_FROM_SIZE: int = 10000
    DEFAULT_TIMEOUT_MS: int = 2000
    ALLOW_PROFILE: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
