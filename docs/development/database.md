# Database

PostgreSQL persistence foundation: SQLAlchemy 2.x ORM, psycopg 3, and Alembic. Agents and the CLI do **not** use the database yet.

Conceptual model: [Data architecture](../architecture/data.md). Decision: [ADR 001](../adr/001-postgresql.md).

## Package layout

```text
app/db/
├── __init__.py          # Public exports
├── base.py              # Declarative Base, UUID/timestamp mixins
├── session.py           # Lazy engine + sessionmaker
└── models/              # Typed ORM mappings
alembic/
├── env.py               # Reads DATABASE_URL from Settings
└── versions/            # Migration scripts
alembic.ini
```

Importing `app.db` or `app.db.session` does **not** open a connection and does not require `DATABASE_URL`.

## Configuration

`Settings.database_url` maps to `DATABASE_URL`. See [Config and secrets](config.md).

SQLAlchemy-compatible URL (psycopg 3 driver):

```text
postgresql+psycopg://USER:PASSWORD@HOST:5432/DATABASE
```

Do not commit a real URL. Copy `.env.example` to `.env` and set `DATABASE_URL` locally.

`postgres://` and `postgresql://` URLs are rewritten to `postgresql+psycopg://` when the engine is created. The URL is never logged.

## Alembic

`alembic/env.py` uses the same `Base.metadata` as the ORM models and reads `DATABASE_URL` from application settings. `alembic.ini` does not contain a real connection string.

```bash
uv run alembic current
uv run alembic upgrade head
uv run alembic downgrade -1
uv run alembic revision --autogenerate -m "describe the change"
```

Review autogenerate output before applying it. Do not run destructive migrations without checking the script.

Initial revision: `244a3d756668_initial_schema`.

## Tests

Unit tests inspect model metadata and configuration. They do **not** require PostgreSQL or a network.

Integration tests that apply migrations against a real PostgreSQL database are a **future step**. Docker/testcontainers are not part of this foundation.

## What this layer is not

- Not a repository or service layer
- Not Agent → DB integration
- Not Supabase Auth, Storage, or SDK usage
- Not object storage, queues, cache, or workflow state
