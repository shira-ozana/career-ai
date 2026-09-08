# Career AI documentation

Career AI helps a user manage and optimize the job-search process.

The **running codebase** is still a Profile Analyzer CLI (structured JSON in, structured analysis out). The **product MVP and target architecture** are documented separately from that implementation.

## Where to document what

| You want to describe… | Write in |
|-----------------------|----------|
| System shape, layers, package layout | [`architecture/`](architecture/overview.md) |
| Persistent domain, ingestion, data access | [`architecture/data.md`](architecture/data.md) |
| A specific implemented feature or component | [`design/`](design/profile-agent.md) |
| A durable architectural decision | `adr/` (create when needed) |
| An end-to-end user or system path | `flows/` (create when needed) |
| Setup, tooling, testing, conventions | [`development/`](development/documentation.md) |

See [Documentation guidelines](development/documentation.md) for when a code change needs a docs update.

## Current status

```mermaid
flowchart LR
    subgraph Implemented["Implemented"]
        A[CLI]
        B[ProfileInput / ProfileAnalysis]
        C[ProfileAnalyzerAgent]
        D[StructuredLLM]
        E[Prompts]
        F[Tests]
        G[Config / .env]
    end

    subgraph Target["Proposed — not implemented"]
        H[Profile ingestion CV / LinkedIn]
        I[Canonical Candidate Profile]
        J[LinkedIn optimization]
        K[Job catalog / matching]
        L[CV tailoring]
        M[Orchestration]
        N[Data access layer]
    end

    A --> C
    B --> C
    E --> C
    D --> C
    C -.-> H
    H -.-> I
```

Details: [Architecture overview](architecture/overview.md) · [Data architecture](architecture/data.md)

## Quick start

```bash
uv sync --extra dev
cp .env.example .env   # if you do not have .env yet
# Add OPENAI_API_KEY in .env

uv run career-ai analyze-profile examples/sample_profile.json
uv run pytest
```

Preview these docs locally:

```bash
uv sync --extra dev --extra docs
uv run mkdocs serve
```
