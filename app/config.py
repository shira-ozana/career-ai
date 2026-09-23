"""Application settings loaded from environment variables."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

# Documented Cursor SDK quick-start model. Local agents require a model id.
# Override with CURSOR_MODEL. This is not discovered via a live catalog call.
DEFAULT_CURSOR_MODEL = "composer-2.5"


class Settings(BaseSettings):
    """Runtime configuration for Career AI Assistant."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    cursor_api_key: str = ""
    cursor_model: str = DEFAULT_CURSOR_MODEL
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

    def require_cursor_api_key(self) -> str:
        key = self.cursor_api_key.strip()
        if not key:
            msg = (
                "CURSOR_API_KEY is not set. "
                "Add it to .env or the environment before using --provider cursor."
            )
            raise ValueError(msg)
        return key

    def cursor_model_name(self) -> str:
        model = self.cursor_model.strip()
        return model or DEFAULT_CURSOR_MODEL

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
