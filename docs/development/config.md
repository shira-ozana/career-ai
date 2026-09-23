# Config and secrets

## Main file

`app/config.py` – loads settings from environment variables / `.env`.

## How it works

```mermaid
flowchart LR
    ENV[.env file] --> PS[pydantic-settings]
    OS[Environment variables] --> PS
    PS --> Settings[Settings]
    Settings --> get_settings["get_settings() cached"]
    get_settings --> LLM[StructuredLLM]
    get_settings --> CLI[CLI logging]
    get_settings --> DB[Engine / Alembic]
```

## `Settings` fields

| Field | Env var | Default | Used for |
|-------|---------|---------|----------|
| `openai_api_key` | `OPENAI_API_KEY` | `""` | OpenAI auth |
| `openai_model` | `OPENAI_MODEL` | `gpt-4o-mini` | OpenAI model name |
| `cursor_api_key` | `CURSOR_API_KEY` | `""` | Cursor auth for `--provider cursor` |
| `cursor_model` | `CURSOR_MODEL` | `composer-2.5` | Cursor model id |
| `log_level` | `LOG_LEVEL` | `INFO` | CLI log level |
| `database_url` | `DATABASE_URL` | `""` | SQLAlchemy PostgreSQL URL |

### Important behavior

1. `env_file=".env"` – reads the local file automatically.
2. `extra="ignore"` – unknown `.env` keys (e.g. `GITHUB_TOKEN`) do **not** break loading.
3. `get_settings()` is wrapped with `@lru_cache` – created once per process.
4. `require_openai_api_key()` raises a clear error if the key is missing.
5. `require_cursor_api_key()` raises a clear error if the Cursor key is missing. The CLI prints that error and exits `1` when `--provider cursor` is selected.
6. `require_database_url()` raises a clear error if the URL is missing. The Profile Analyzer CLI does not call it.

## Environment files

### `.env` (local, not in git)

Contains real secrets:

```bash
OPENAI_API_KEY=...
OPENAI_MODEL=gpt-4o-mini
CURSOR_API_KEY=...
CURSOR_MODEL=composer-2.5
LOG_LEVEL=INFO
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST:5432/DATABASE
GITHUB_USERNAME=shira-ozana
GITHUB_TOKEN=...
```

Use a real URL only in local `.env`. Never commit it. `.env.example` contains a commented placeholder only.

### `.env.example` (tracked in git)

Safe template without real secrets – documents which variables are needed.

## Who consumes config?

| Consumer | What it uses |
|----------|--------------|
| `StructuredLLM` | `openai_api_key`, `openai_model` |
| `CursorStructuredLLMClient` | `cursor_api_key`, `cursor_model` |
| `cli.py` | `log_level`, and which extraction provider to construct |
| `app/db/session.py`, Alembic | `database_url` (when creating an engine or migrating) |
| `scripts/git-push.sh` | `GITHUB_USERNAME`, `GITHUB_TOKEN` (directly from `.env`, not via Settings) |

> Note: `GITHUB_TOKEN` is only for git push. The Profile Agent itself does not need it.

## Common failure flow

```mermaid
flowchart TD
    A[Run analyze-profile] --> B{OPENAI_API_KEY set?}
    B -->|no| C[Clear ValueError]
    B -->|yes| D[AsyncOpenAI client]
    D --> E[Call OpenAI]
```

## Why pydantic-settings?

- Type-safe: config mistakes fail early
- Self-documenting: class fields are the spec
- Easy to test: you can pass `Settings(...)` manually into `StructuredLLM`

## Security rules

1. Never commit `.env`
2. Never paste tokens into chat / README
3. When switching machines – copy `.env` separately (not via GitHub)
4. `.gitignore` already ignores `.env` and `.env.*` (except `.env.example`)
