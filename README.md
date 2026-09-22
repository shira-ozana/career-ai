# Career AI Assistant

Personal career manager powered by AI agents.

Career AI helps a user manage and optimize the job-search process: ingest CV and LinkedIn sources, analyze the candidate profile, recommend LinkedIn improvements, discover and rank jobs, and tailor a CV for a selected match.

## Status

**Implemented:** Profile Analyzer Agent (CLI) with OpenAI Structured Outputs, plus a PostgreSQL persistence foundation (SQLAlchemy / Alembic) that is not yet used by agents.

Career AI is a **modular monolith** (one backend, one PostgreSQL database), not a microservice system. **Product MVP and planned architecture** (ingestion, catalog-first job search, matching, CV tailoring, application services) are documented in [`docs/`](./docs/index.md).

## Documentation

Detailed docs live in [`docs/`](./docs/index.md) and are built with MkDocs.

| Folder | Use for |
|--------|---------|
| [`docs/architecture/`](./docs/architecture/overview.md) | Modular monolith, [data model](./docs/architecture/data.md), [Job Search](./docs/architecture/job-search.md), package layout |
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

- Typed Profile Analyzer input/output via Pydantic (`ProfileInput` / `ProfileAnalysis`; not the persisted Candidate Profile)
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
│   ├── agents/          # Agent capabilities (profile implemented)
│   ├── db/              # SQLAlchemy models, engine, sessions
│   ├── models/          # Agent I/O contracts (Pydantic)
│   ├── prompts/         # Prompt templates
│   ├── tools/           # Shared tools (LLM client, etc.)
│   ├── workflows/       # Empty scaffold; proposed application/workflow
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

See [Architecture](./docs/architecture/overview.md), [Data architecture](./docs/architecture/data.md), and [Job Search](./docs/architecture/job-search.md). PostgreSQL is the selected database ([ADR 001](./docs/adr/001-postgresql.md)). The system is a modular monolith ([ADR 002](./docs/adr/002-modular-monolith.md)).

Direction, not a delivery schedule:

1. **Next:** Profile Ingestion Service — structured JSON → canonical `CandidateProfile` in PostgreSQL
2. Profile ingestion from CV and LinkedIn, with conflict handling
3. LinkedIn optimization
4. Catalog-first Job Search (`SearchExecution`, discovery, matching)
5. CV tailoring
6. HTTP API when an interface beyond CLI is needed

Do not treat queues, workers, or a Job Search microservice as current work.

## Learning goals

- Professional Python (typing, Pydantic, async, testing)
- Modern AI tooling (OpenAI, Structured Outputs, agents)
- Portfolio-grade modular monolith with extractable module boundaries
