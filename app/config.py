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
    database_url: str = ""

    def require_openai_api_key(self) -> str:
        if not self.openai_api_key:
            msg = (
                "OPENAI_API_KEY is not set. "
                "Copy .env.example to .env and add your key."
            )
            raise ValueError(msg)
        return self.openai_api_key

    def require_database_url(self) -> str:
        if not self.database_url.strip():
            msg = (
                "DATABASE_URL is not set. "
                "Copy .env.example to .env and add a SQLAlchemy PostgreSQL URL."
            )
            raise ValueError(msg)
        return self.database_url.strip()


@lru_cache
def get_settings() -> Settings:
    return Settings()
