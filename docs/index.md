# Career AI documentation

Career AI helps a user manage and optimize the job-search process.

The **running codebase** is a Profile Analyzer CLI, a text profile-extraction CLI, and a PostgreSQL schema that is not wired to either flow. The deployable shape is a **modular monolith** — one backend, one database — not microservices.

The **product MVP and planned architecture** are documented separately from that implementation.

## Where to document what

| You want to describe… | Write in |
|-----------------------|----------|
| System shape, layers, package layout | [`architecture/`](architecture/overview.md) |
| Persistent domain, ingestion, data access | [`architecture/data.md`](architecture/data.md) |
| Job Search pipeline (planned) | [`architecture/job-search.md`](architecture/job-search.md) |
| A specific implemented feature or component | [`design/`](design/profile-agent.md) |
| A durable architectural decision | [`adr/`](adr/001-postgresql.md) |
| An end-to-end user or system path | [`flows/`](flows/profile-ingestion.md) |
| Setup, tooling, testing, conventions | [`development/`](development/documentation.md) |

See [Documentation guidelines](development/documentation.md) for when a code change needs a docs update.

## Current status

```mermaid
flowchart LR
    subgraph Implemented["Implemented"]
        A[CLI]
        B[ProfileInput / ProfileAnalysis]
        C[ProfileAnalyzerAgent]
        T[Text extraction flow]
        D[StructuredLLM]
        E[Prompts]
        F[Tests]
        G[Config / .env]
        P[PostgreSQL schema / Alembic]
    end

    subgraph Next["Not implemented"]
        Repo[Canonical profile repository]
        H[File / URL acquisition]
        R[Reconciliation / HITL]
    end

    subgraph Planned["Planned — not implemented"]
        K[SearchExecution / catalog-first search]
        L[Matching / JobMatch wiring]
        M[CV tailoring]
    end

    A --> C
    B --> C
    A --> T
    E --> C
    E --> T
    D --> C
    D --> T
    T -.-> H
    T -.-> R
    R -.-> Repo
    Repo -.-> P
    K -.-> L
```

Details: [Architecture overview](architecture/overview.md) · [Data architecture](architecture/data.md) · [Job Search](architecture/job-search.md)

## Quick start

```bash
uv sync --extra dev
cp .env.example .env   # if you do not have .env yet
# Add OPENAI_API_KEY in .env

uv run career-ai analyze-profile examples/sample_profile.json
uv run career-ai extract-profile examples/sample_profile_ingestion.json --mock
# optional, needs CURSOR_API_KEY:
# uv run career-ai extract-profile examples/sample_profile_ingestion.json --provider cursor
uv run pytest
```

Preview these docs locally:

```bash
uv sync --extra dev --extra docs
uv run mkdocs serve
```
