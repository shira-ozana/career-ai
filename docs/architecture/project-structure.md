# Project structure

## Directory tree (what exists)

```text
career-ai/
├── app/                         # Application code
│   ├── __init__.py
│   ├── __main__.py              # Enables: python -m app
│   ├── cli.py                   # Terminal entrypoint
│   ├── config.py                # Settings from .env
│   ├── agents/                  # All agents
│   │   ├── profile/             # Implemented
│   │   │   ├── __init__.py
│   │   │   └── agent.py
│   │   ├── linkedin/            # Placeholder
│   │   ├── resume/              # Placeholder
│   │   ├── jobs/                # Placeholder
│   │   ├── coach/               # Placeholder
│   │   ├── content/             # Placeholder
│   │   └── skills/              # Placeholder
│   ├── models/                  # Shared Pydantic models
│   │   └── profile.py           # Done
│   ├── prompts/                 # Prompt templates
│   │   └── profile.py           # Done
│   ├── tools/                   # Shared tools (LLM, etc.)
│   │   └── llm.py               # Done
│   ├── memory/                  # Empty scaffold; not part of current MVP
│   ├── workflows/               # Empty scaffold – proposed orchestration
│   └── api/                     # Empty scaffold – future HTTP API
├── tests/                       # Tests
├── examples/                    # Sample inputs
├── docs/                        # MkDocs site – see below
├── scripts/                     # Helpers (git push)
├── docker/                      # Future
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
│   ├── overview.md             # Product, target vs implemented architecture
│   ├── data.md                 # Persistence, ingestion, conceptual data model
│   └── project-structure.md    # This page
├── design/                     # Implemented feature and component design
└── development/                # Setup, testing, documentation conventions
```

`adr/` and `flows/` are created when the first architectural decision or end-to-end flow is written. Do not add empty placeholder pages. The database engine is still an [open question](data.md#database-decision-open); add an ADR when it is decided.

Guidelines: [Documentation](../development/documentation.md).

## Why this layout?

```mermaid
flowchart TB
    subgraph Entry["Entry layer"]
        CLI[cli.py / __main__.py]
        API[api/ future]
    end

    subgraph Domain["Business logic"]
        Agents[agents/*]
        Workflows[workflows/ future]
    end

    subgraph Shared["Shared infrastructure"]
        Models[models/]
        Prompts[prompts/]
        Tools[tools/]
        Config[config.py]
        Memory[memory/ unused scaffold]
    end
    end

    CLI --> Agents
    API -.-> Agents
    Agents --> Models
    Agents --> Prompts
    Agents --> Tools
    Tools --> Config
    Workflows -.-> Agents
    Agents -.-> Memory
```

### Key principle

- **`agents/`** = what the system can do (capabilities)
- **`models/`** = how data looks (contracts)
- **`prompts/`** = how we talk to the LLM (instructions)
- **`tools/`** = how we connect outward (OpenAI, etc.)
- **`cli.py` / `api/`** = how the user invokes the system

This lets us replace CLI with an API later without rewriting the agent.

## File → responsibility map

| File | Single responsibility |
|------|------------------------|
| `app/config.py` | Load settings and secrets |
| `app/models/profile.py` | Validate and shape profile data |
| `app/prompts/profile.py` | LLM instruction text |
| `app/tools/llm.py` | Call OpenAI + parse structured output |
| `app/agents/profile/agent.py` | Run the analysis flow |
| `app/cli.py` | Read JSON file and print result |
| `tests/*` | Verify contracts and flow |

## What does "placeholder" mean?

Folders like `app/agents/jobs/` currently contain only empty / nearly empty `__init__.py` files.

This is intentional: they reserve a place in the package tree without premature implementation.

They are **not** a frozen map of the [target architecture](overview.md#target-architecture-proposed). Current product components are Profile Ingestion / Analysis, LinkedIn Optimization, Job Search / Matching, CV Tailoring, and Orchestration. Folders such as `coach`, `content`, `skills`, and `memory/` come from an earlier scaffold and are outside the current product MVP.

## Root-level project files

| File | Role |
|------|------|
| `pyproject.toml` | Package name, dependencies, `career-ai` script, pytest/ruff config |
| `uv.lock` | Exact versions for reproducible installs |
| `.env` | Local secrets (`OPENAI_API_KEY`, `GITHUB_TOKEN`) – **not in git** |
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
