# Career AI Assistant

Personal career manager powered by AI agents.

Career AI helps a user manage and optimize the job-search process: ingest CV and LinkedIn sources, analyze the candidate profile, recommend LinkedIn improvements, discover and rank jobs, and tailor a CV for a selected match.

## Status

**Implemented:** Profile Analyzer Agent (CLI) with OpenAI Structured Outputs, plus a PostgreSQL persistence foundation (SQLAlchemy / Alembic) that is not yet used by agents.

**Product MVP and target architecture** (ingestion, matching, CV tailoring, orchestration, data-access layer) are documented in [`docs/`](./docs/index.md).

## Documentation

Detailed docs live in [`docs/`](./docs/index.md) and are built with MkDocs.

| Folder | Use for |
|--------|---------|
| [`docs/architecture/`](./docs/architecture/overview.md) | Product, system architecture, [data model](./docs/architecture/data.md), package layout |
| [`docs/design/`](./docs/design/profile-agent.md) | Feature / component design |
| [`docs/adr/`](./docs/adr/001-postgresql.md) | Architectural decisions |
| `docs/flows/` | End-to-end flows (create when needed) |
| [`docs/development/`](./docs/development/documentation.md) | Setup, testing, and documentation conventions |

When a code change affects architecture, contracts, flows, or conventions, update the matching folder **in the same PR**. See [Documentation guidelines](./docs/development/documentation.md).

```bash
uv sync --extra dev --extra docs
uv run mkdocs serve
```

## Features (current)

- Typed profile input/output via Pydantic
- Profile Analyzer Agent (`score`, strengths, weaknesses, missing skills, recommendations)
- OpenAI Structured Outputs integration
- CLI for local analysis
- PostgreSQL schema via SQLAlchemy 2.x and Alembic (not connected to agents yet)
- Unit tests with mocked LLM

Product capabilities beyond this CLI are listed in [Architecture](./docs/architecture/overview.md).

## Project layout

```text
career-ai/
├── app/
│   ├── agents/          # Independent agents (profile first)
│   ├── db/              # SQLAlchemy models, engine, sessions
│   ├── models/          # Pydantic domain models
│   ├── prompts/         # Prompt templates
│   ├── tools/           # Shared tools (LLM client, etc.)
│   ├── memory/          # Empty scaffold; not current MVP
│   ├── workflows/       # Empty scaffold; proposed orchestration
│   └── api/             # Empty scaffold; future HTTP API
├── alembic/             # Database migrations
├── examples/            # Sample payloads
├── tests/
├── docs/                # architecture, design, development
├── mkdocs.yml
└── pyproject.toml
```

## Requirements

- Python 3.13+
- [uv](https://github.com/astral-sh/uv)
- OpenAI API key
- PostgreSQL (optional until you run migrations; hosted development DB is Supabase Postgres)

## Setup

```bash
cd ~/Downloads/career-ai
uv sync --extra dev
cp .env.example .env
# Edit .env and set OPENAI_API_KEY
# Set DATABASE_URL when you are ready to run migrations (see docs/development/database.md)
```

## Run Profile Agent

```bash
uv run career-ai analyze-profile examples/sample_profile.json
```

Or:

```bash
uv run python -m app.cli analyze-profile examples/sample_profile.json
```

Example output shape:

```json
{
  "score": 71,
  "strengths": ["Python", "Backend"],
  "weaknesses": ["Limited AI Agents portfolio evidence"],
  "missing_skills": ["RAG", "MCP", "AI Agents"],
  "recommendations": ["Improve headline", "Add measurable achievements"]
}
```

## Tests

```bash
uv run pytest
```

## Roadmap

See [Architecture](./docs/architecture/overview.md) and [Data architecture](./docs/architecture/data.md) for the current product MVP. PostgreSQL is the selected database ([ADR 001](./docs/adr/001-postgresql.md)).

Direction, not a delivery schedule:

1. Profile ingestion from CV and LinkedIn, with conflict handling
2. Wire agents to the canonical Candidate Profile schema
3. LinkedIn optimization, job catalog/matching, CV tailoring
4. Orchestration and a data-access layer
5. HTTP API when an interface beyond CLI is needed

## Learning goals

- Professional Python (typing, Pydantic, async, testing)
- Modern AI tooling (OpenAI, Structured Outputs, agents)
- Portfolio-grade multi-agent system design
