"""Lazy SQLAlchemy engine and session factory.

Importing this module does not open a database connection and does not
require DATABASE_URL to be set.
"""

from __future__ import annotations

from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings


def sqlalchemy_database_url(url: str) -> str:
    """Return a SQLAlchemy URL that uses the psycopg3 driver.

    Accepts ``postgresql://`` and ``postgres://`` (common hosted-provider
    forms) and rewrites them to ``postgresql+psycopg://``. Already-qualified
    URLs are returned unchanged. The URL itself is never logged.
    """
    stripped = url.strip()
    if stripped.startswith("postgresql+psycopg://"):
        return stripped
    if stripped.startswith("postgresql://"):
        return "postgresql+psycopg://" + stripped.removeprefix("postgresql://")
    if stripped.startswith("postgres://"):
        return "postgresql+psycopg://" + stripped.removeprefix("postgres://")
    return stripped


@lru_cache
def get_engine() -> Engine:
    settings = get_settings()
    url = sqlalchemy_database_url(settings.require_database_url())
    return create_engine(url, pool_pre_ping=True)


@lru_cache
def get_session_factory() -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine())


def get_session() -> Session:
    """Return a new Session. The caller is responsible for closing it."""
    return get_session_factory()()
