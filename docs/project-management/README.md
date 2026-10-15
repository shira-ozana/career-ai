# Project management

This section records how Career AI is organized, what the repository implements today, and which product decisions are still open.

Application code, Alembic migrations, and tests are the source of truth for current behavior. Architecture pages, ADRs, and design pages are the source of truth for accepted technical design. This section summarizes those documents and keeps the project workflow, status, and in-progress design discussions that are not yet ADRs.

Chat history is supporting context. A conversation can propose a design. The repository is what later work treats as durable.

## Status vocabulary

| Label | Meaning |
|-------|---------|
| **Implemented** | Present in application code, migrations, or tests. |
| **Designed / decided** | Accepted in an ADR or in the architecture and design docs. The behavior is specified. Say separately when only a schema or a request contract exists. |
| **In design** | Under active design. Some rules are accepted. Schema, lifecycle, or policy is still open. |
| **Planned** | Expected work. The direction is known. Implementation has not started, or only a placeholder or request field exists. |
| **Future / deferred** | Direction worth keeping. Not a selected dependency. |

A table can be implemented while the workflow that writes it is still planned. Pages here say which of those is true.

## How this relates to the rest of the docs

| Question | Read |
|----------|------|
| What does the running code do? | [Architecture overview](../architecture/overview.md), [Project structure](../architecture/project-structure.md) |
| What is persisted? | [Data architecture](../architecture/data.md), [Database](../development/database.md) |
| Why was a structural choice made? | [ADR 001](../adr/001-postgresql.md) and the other records under `docs/adr/` |
| How does an implemented component work? | [Design](../design/profile-ingestion.md) |
| What is the end-to-end path? | [Profile ingestion flow](../flows/profile-ingestion.md) |
| What is implemented, decided, or still open? | This section |
| How should a feature be developed? | [Working agreement](working-agreement.md) |

Coding assistants also follow `AGENTS.md` at the repository root.

When a page here and a technical page disagree, the discrepancy stays visible in the [Decision register](decision-register.md). This section does not silently pick a winner.

## Contents

- [Working agreement](working-agreement.md) — conversations, feature process, and documentation checkpoints
- [Project status](project-status.md) — repository snapshot
- [Roadmap](roadmap.md) — feature areas by status, with no dates
- [Decision register](decision-register.md) — accepted decisions and unresolved discrepancies
- [Profile ingestion](features/profile-ingestion.md)
- [Profile reconciliation](features/profile-reconciliation.md)
- [Job search](features/job-search.md)
- [Job matching](features/job-matching.md)
- [CV tailoring](features/cv-tailoring.md)

Conventions for where a technical change is documented: [Documentation guidelines](../development/documentation.md).
