"""Application settings loaded from environment variables."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for Career AI Assistant."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    log_level: str = "INFO"

    def require_openai_api_key(self) -> str:
        if not self.openai_api_key:
            msg = (
                "OPENAI_API_KEY is not set. "
                "Copy .env.example to .env and add your key."
            )
            raise ValueError(msg)
        return self.openai_api_key


@lru_cache
def get_settings() -> Settings:
    return Settings()
