"""Tests for database configuration and lazy engine setup."""

from __future__ import annotations

import pytest

from app.config import Settings
from app.db.session import get_engine, get_session_factory, sqlalchemy_database_url


def test_database_url_defaults_empty_without_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    settings = Settings(_env_file=None)
    assert settings.database_url == ""


def test_require_database_url_raises_when_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    settings = Settings(database_url="  ", _env_file=None)
    with pytest.raises(ValueError, match="DATABASE_URL"):
        settings.require_database_url()


def test_require_database_url_strips_whitespace(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    settings = Settings(
        database_url="  postgresql+psycopg://career:secret@localhost:5432/career  ",
        _env_file=None,
    )
    assert settings.require_database_url() == "postgresql+psycopg://career:secret@localhost:5432/career"


def test_sqlalchemy_url_rewrites_common_postgres_schemes() -> None:
    host_path = "career:secret@localhost:5432/career"
    assert sqlalchemy_database_url(f"postgresql://{host_path}") == f"postgresql+psycopg://{host_path}"
    assert sqlalchemy_database_url(f"postgres://{host_path}") == f"postgresql+psycopg://{host_path}"
    already = f"postgresql+psycopg://{host_path}"
    assert sqlalchemy_database_url(already) == already


def test_importing_session_does_not_create_engine() -> None:
    assert get_engine.cache_info().currsize == 0
    assert get_session_factory.cache_info().currsize == 0
