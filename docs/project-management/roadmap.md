# Roadmap

This roadmap is a status map. It has no dates and no estimates.

Labels are defined in [Project management](README.md). "Schema" means SQLAlchemy mappings and the initial Alembic revision. "Runtime" means a path the CLI or an application service actually executes.

Sources: the repository tree, [Architecture overview](../architecture/overview.md), [Data architecture](../architecture/data.md), [Job Search](../architecture/job-search.md), [Future architecture](../architecture/future-architecture.md), and the design discussion preserved under [Features](features/profile-reconciliation.md).

## Status by area

| Area | Status | What that means in this repo |
|------|--------|------------------------------|
| Repository and Python foundation | **Implemented** | `pyproject.toml`, uv lockfile, `app/` package, Ruff, pytest, `examples/` |
| Documentation site | **Implemented** | MkDocs, `docs/`, `.github/workflows/ci.yml` docs job |
| Database foundation | **Implemented** as schema and session helpers | Not called by the CLI. [Database](../development/database.md) |
| Profile Analyzer | **Implemented** | Scores a `ProfileInput` JSON file. Does not persist |
| Profile ingestion, text extraction | **Implemented** | Text sources only. Per-source `ExtractedCandidateProfile`. No database write |
| Cursor LLM provider | **Implemented** | Optional adapter for `extract-profile`. [LLM client](../design/llm-client.md) |
| Profile reconciliation | **In design** | Rules recorded. No module. Open questions remain |
| Human-in-the-loop review | **Designed / decided** as a requirement; runtime **not started** | No review tables or pause/resume runtime |
| Canonical profile persistence from ingestion | **Designed / decided** as the merge direction; runtime **not started** | `CandidateProfile` exists. Ingestion does not write it |
| File / PDF ingestion | **Planned** | `FileProfileSource` is a request field. The file is not opened |
| URL / LinkedIn ingestion | **Planned** | `UrlProfileSource` is a request field. The URL is not fetched |
| Job search | **Designed / decided** pipeline; runtime **planned** | [ADR 004](../adr/004-catalog-first-job-search.md). `SearchExecution` is not in the schema |
| Job matching | **Designed / decided**; scoring runtime **planned** | `JobMatch` rows are mapped. Nothing creates them |
| CV tailoring | **Designed / decided** as `ResumeVersion`; generation **planned** | No separate `TailoredCV` entity. No generator |
| LinkedIn optimization | **Planned** | `app/agents/linkedin/` placeholder |
| Authentication and authorization | **Designed / decided** rules; flows **not implemented** | Identity tables only |
| GitHub collaboration / CI | **Implemented** for the three CI checks | Branch protection is not defined in the workflow file. [Continuous integration](../development/ci.md) |
| LLM evaluation and observability | **Future / deferred** platform; principles **designed / decided** | [Future architecture](../architecture/future-architecture.md#evaluation) |
| Resumable workflow engine (LangGraph as a candidate) | **Future / deferred** | Not a dependency. Not selected |
| Job Search as its own service | **Future / deferred** | The running system is a modular monolith |
| HTTP API | **Future / deferred** | Empty `app/api/` scaffold |
| Model router, prompt registry, execution-metadata storage | **Future / deferred** | The provider protocol itself is **implemented** |

## Sequences already written down

These sequences exist in the repository or in the design discussion. This roadmap does not merge them into a new order.

**README direction** (called a direction, not a schedule): text extraction is the done slice; then canonical merge, then file/URL acquisition and reconciliation; then LinkedIn optimization, catalog-first job search, CV tailoring, and an HTTP API when a non-CLI interface is needed.

**Architecture overview:** text extraction is implemented. The stated next implementation milestone is an application-owned merge into `CandidateProfile` with no implicit deletion, plus repositories. File and URL acquisition and reconciliation are described there as still later. See [Next implementation milestone](../architecture/overview.md#next-implementation-milestone).

**Active design thread:** Profile reconciliation is in design, and its open questions include how an approved decision updates the canonical profile. Canonical writes, file acquisition, and URL acquisition have not started.

The difference in order is recorded under [Unresolved discrepancies](decision-register.md#unresolved-discrepancies). It is not resolved here.

## Explicitly not current work

- microservices, a second database, or distributed transactions
- `SearchExecution` / `SourceExecution` tables
- queues, workers, and a broker choice
- LangGraph or any other workflow engine
- object storage for CV and resume files
- anonymous job-catalog browsing
- education / institution tables
- an evaluation platform, shadow/canary/A/B, or drift monitoring

Job Search's own deferred list: [Intentionally deferred for this flow](../architecture/job-search.md#intentionally-deferred-for-this-flow).
