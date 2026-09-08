# Career AI Assistant

Personal career manager powered by AI agents.

Career AI helps a user manage and optimize the job-search process: ingest CV and LinkedIn sources, analyze the candidate profile, recommend LinkedIn improvements, discover and rank jobs, and tailor a CV for a selected match.

## Status

**Implemented:** Profile Analyzer Agent (CLI) with OpenAI Structured Outputs.

**Product MVP and target architecture** (ingestion, persistence, matching, CV tailoring, orchestration) are documented in [`docs/`](./docs/index.md) and are not implemented yet.

## Documentation

Detailed docs live in [`docs/`](./docs/index.md) and are built with MkDocs.

| Folder | Use for |
|--------|---------|
| [`docs/architecture/`](./docs/architecture/overview.md) | Product, system architecture, [data model](./docs/architecture/data.md), package layout |
| [`docs/design/`](./docs/design/profile-agent.md) | Feature / component design |
| `docs/adr/` | Architectural decisions (create when needed) |
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
- Unit tests with mocked LLM

Product capabilities beyond this CLI are listed in [Architecture](./docs/architecture/overview.md).

## Project layout

```text
career-ai/
├── app/
│   ├── agents/          # Independent agents (profile first)
│   ├── models/          # Pydantic domain models
│   ├── prompts/         # Prompt templates
│   ├── tools/           # Shared tools (LLM client, etc.)
│   ├── memory/          # Empty scaffold; not current MVP
│   ├── workflows/       # Empty scaffold; proposed orchestration
│   └── api/             # Empty scaffold; future HTTP API
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

## Setup

```bash
cd ~/Downloads/career-ai
uv sync --extra dev
cp .env.example .env
# Edit .env and set OPENAI_API_KEY
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

See [Architecture](./docs/architecture/overview.md) and [Data architecture](./docs/architecture/data.md) for the current product MVP and open questions (including database selection).

Direction, not a delivery schedule:

1. Profile ingestion from CV and LinkedIn, with conflict handling
2. Canonical Candidate Profile persistence
3. LinkedIn optimization, job catalog/matching, CV tailoring
4. Orchestration and a data-access layer
5. HTTP API when an interface beyond CLI is needed

## Learning goals

- Professional Python (typing, Pydantic, async, testing)
- Modern AI tooling (OpenAI, Structured Outputs, agents)
- Portfolio-grade multi-agent system design
