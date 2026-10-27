from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Experiment API"
    app_version: str = "0.1.0"
    api_port: int = 4000
    
    # HAWKI provider settings
    hawki_base_url: str = "http://localhost:8080/v1"
    hawki_api_key: str = "ALLOWED_KEYS"
    hawki_request_timeout: int = 90
    prompts_dir: str = "prompts"
    
    # OpenAI provider settings (for future use)
    openai_api_key: str | None = None
    openai_request_timeout: int = 90

    # OpenRouter provider settings for Marker LLM mode
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("OPEN_ROUTER_API_KEY", "OPEN_ROUTER_API_KEY_FREE"),
    )
    openrouter_model: str = "google/gemma-4-26b-a4b-it"

    # OpenRouter-compatible local/test setups may provide this key in .env.
    open_router_api_key: str | None = None
    open_router_api_key_free: str | None = Field(default=None, validation_alias="OPEN_ROUTER_API_KEY_FREE")

    # LocalAI provider settings (OpenAI-compatible local endpoint)
    localai_base_url: str = "http://localai.kibutler.leipzig.sup-sahlmann.com/v1"
    localai_api_key: str = "not-needed"
    localai_request_timeout: int = 90
    localai_retry_attempts: int = 3
    localai_retry_backoff_seconds: float = 2.0

    # OpenRouter retry settings (rate-limit-aware, free tier: 16 req/min)
    openrouter_retry_attempts: int = 4
    openrouter_retry_backoff_seconds: float = 15.0

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
