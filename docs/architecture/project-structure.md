# Project structure

## Directory tree (what exists)

```text
career-ai/
├── app/                         # Application code
│   ├── __init__.py
│   ├── __main__.py              # Enables: python -m app
│   ├── cli.py                   # Terminal entrypoint
│   ├── config.py                # Settings from .env
│   ├── db/                      # SQLAlchemy persistence foundation
│   │   ├── base.py              # Declarative Base + mixins
│   │   ├── session.py           # Lazy engine / sessionmaker
│   │   └── models/              # ORM mappings
│   ├── agents/                  # All agents
│   │   ├── profile/             # Implemented
│   │   │   ├── __init__.py
│   │   │   └── agent.py
│   │   ├── linkedin/            # Placeholder (proposed MVP)
│   │   ├── resume/              # Placeholder (proposed MVP)
│   │   └── jobs/                # Placeholder (proposed MVP)
│   ├── models/                  # Agent I/O contracts (Pydantic)
│   │   └── profile.py           # Profile Analyzer input/output
│   ├── prompts/                 # Prompt templates
│   │   └── profile.py           # Done
│   ├── tools/                   # Shared tools (LLM, etc.)
│   │   └── llm.py               # Done
│   ├── workflows/               # Empty scaffold – proposed application/workflow
│   └── api/                     # Empty scaffold – future HTTP API
├── alembic/                     # Migrations
│   ├── env.py
│   └── versions/
├── tests/                       # Tests
├── examples/                    # Sample inputs
├── docs/                        # MkDocs site – see below
├── scripts/                     # Helpers (git push)
├── alembic.ini
├── mkdocs.yml                   # Docs site navigation
├── pyproject.toml               # Dependencies + tooling config
├── uv.lock                      # Locked dependency versions
├── .env.example                 # Secret template (no real values)
├── .env                         # Local secrets (not in git)
├── .gitignore
└── README.md
```

## Documentation layout

```text
docs/
├── index.md                    # Docs home and folder map
├── architecture/
│   ├── overview.md             # Modular monolith, layers, current vs planned
│   ├── data.md                 # Persistence, ownership, relational schema
│   ├── job-search.md           # Planned catalog-first Job Search
│   └── project-structure.md    # This page
├── design/                     # Implemented feature and component design
├── development/                # Setup, testing, documentation conventions
└── adr/
    ├── 001-postgresql.md
    ├── 002-modular-monolith.md
    ├── 003-application-owns-workflows.md
    └── 004-catalog-first-job-search.md
```

`flows/` is created when the first end-to-end flow is written. Do not add empty placeholder pages.

Guidelines: [Documentation](../development/documentation.md). Database setup: [Database](../development/database.md).

## Why this layout?

```mermaid
flowchart TB
    subgraph Entry["Entry layer"]
        CLI[cli.py / __main__.py]
        API[api/ future]
    end

    subgraph App["Application — decided, mostly not implemented"]
        Workflows[workflows/ scaffold]
        Services[application services planned]
    end

    subgraph Capabilities["Agent capabilities"]
        Agents[agents/*]
    end

    subgraph Shared["Shared infrastructure"]
        Models[models/ agent I/O]
        Prompts[prompts/]
        Tools[tools/]
        Config[config.py]
        DB[db/ persistence ORM]
        Repos[repositories planned]
    end

    CLI --> Agents
    CLI -.-> Services
    API -.-> Services
    Services --> Agents
    Services --> Repos
    Agents --> Models
    Agents --> Prompts
    Agents --> Tools
    Tools --> Config
    Repos --> DB
    DB -.-> Config
    Workflows -.-> Services
```

**Implemented today:** CLI → Profile Analyzer agent. Application services and repositories do not exist yet. They are the next Profile Ingestion milestone, not extra deployables.

### Key principle

- **`agents/`** = capabilities (AI/specialized work), not workflow owners
- **`models/`** = agent input/output contracts (not persistence, not ingestion)
- **`prompts/`** = how we talk to the LLM (instructions)
- **`tools/`** = how we connect outward (OpenAI, etc.)
- **`db/`** = how domain state is stored (SQLAlchemy; not used by agents yet)
- **`cli.py` / `api/`** = how the user invokes the system
- **application services / repositories** = planned; they own persistence, transactions, and authorization

This lets us replace CLI with an API later without rewriting capabilities. The API should call application services, not agents directly. See [ADR 003](../adr/003-application-owns-workflows.md).

## File → responsibility map

| File | Single responsibility |
|------|------------------------|
| `app/config.py` | Load settings and secrets |
| `app/db/` | SQLAlchemy Base, engine/session, ORM models |
| `alembic/` | Schema migrations |
| `app/models/profile.py` | Profile Analyzer I/O contract (`ProfileInput` / `ProfileAnalysis`) |
| `app/prompts/profile.py` | LLM instruction text |
| `app/tools/llm.py` | Call OpenAI + parse structured output |
| `app/agents/profile/agent.py` | Run the analysis flow |
| `app/cli.py` | Read JSON file and print result |
| `tests/*` | Verify contracts and flow |

## What does "placeholder" mean?

Folders like `app/agents/jobs/` currently contain only a short status docstring in `__init__.py`.

This is intentional: they reserve a place in the package tree without premature implementation.

They are **not** a frozen map of the [modular monolith components](overview.md#target-product-components-proposed). Current product components are Profile Ingestion / Analysis, LinkedIn Optimization, Job Discovery, Matching, CV Tailoring, and Application / Workflow. Discovery and Matching may share a package at first; they stay separate responsibilities. Earlier leftover folders (`coach`, `content`, `skills`, `memory`) were removed so the tree matches that map.

## Root-level project files

| File | Role |
|------|------|
| `pyproject.toml` | Package name, dependencies, `career-ai` script, pytest/ruff config |
| `uv.lock` | Exact versions for reproducible installs |
| `alembic.ini` | Alembic config; database URL comes from Settings, not this file |
| `.env` | Local secrets (`OPENAI_API_KEY`, `DATABASE_URL`, `GITHUB_TOKEN`) – **not in git** |
| `.env.example` | Safe shared template |
| `examples/sample_profile.json` | Sample input for CLI runs |

## How Python finds the `app` package

In `pyproject.toml`:

```toml
[tool.pytest.ini_options]
pythonpath = ["."]
```

With `uv sync`, the package is installed in editable mode, so imports like:

```python
from app.agents.profile import ProfileAnalyzerAgent
```

work in both tests and the CLI.
