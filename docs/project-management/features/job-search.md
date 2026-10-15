# Job search

**Designed / decided** as a pipeline. **Not implemented** as a runtime.

The schema has `Job`, `Company`, `JobSearchRequest`, and `JobMatch`. There is no `SearchExecution` table, no catalog refresh, no external provider client, and no code that runs a search. `app/agents/jobs/` is a placeholder docstring.

The design lives in [Job Search](../../architecture/job-search.md) and [ADR 004](../../adr/004-catalog-first-job-search.md). Persistence ownership: [Data architecture](../../architecture/data.md). This page only records status.

## Accepted direction

- Catalog-first search. The internal job catalog participates before external sources. External discovery enriches that catalog.
- Discovery and matching are separate responsibilities, including while both would run in the monolith.
- `JobSearchRequest` is persistent, user-specific search intent. It is not a run of the search.
- `SearchExecution` is one run of that request (`JobSearchRequest` 1:N `SearchExecution`). It is **planned** and not mapped.
- Conceptual execution lifecycle: `PENDING` → `RUNNING` → `COMPLETED` | `PARTIAL` | `FAILED`. `PARTIAL` may mean one provider failed and others completed. This is not an implemented enum.
- Heavy execution is asynchronous. The synchronous part validates, creates or reads the request, creates a `SearchExecution`, starts the work, and returns an identifier and status. No queue or broker is selected.
- Source policy `AUTO` (default) versus `SELECTED` is conceptual. The catalog still participates when no external source is selected. Policy columns are **deferred**.
- Job freshness is separate from the time a search ran. A later important action can verify one job without rerunning the search. Freshness columns are **deferred**.
- `SourceExecution` persistence is **deferred**.
- A future extraction of Job Search into its own service may become justified. It is not the current architecture. [ADR 002](../../adr/002-modular-monolith.md).

Search-specific target title and experience range belong on `JobSearchRequest` (`target_title`, `min_years_experience`, `max_years_experience`, plus `preferred_seniority` and `location`). They are not fields on `CandidateProfile`. An intentional search range can differ from the candidate's actual experience. Nothing in the CLI writes these rows.

## What is easy to mistake for an implementation

| Name in the design | In the repository |
|--------------------|-------------------|
| `SearchExecution` | Not a model, table, or enum |
| `SourceExecution` | Not present. Explicitly deferred |
| Catalog refresh | Not present |
| External job providers | Not present |
| Async worker | Not present. No queue dependency |
| `AUTO` / `SELECTED` | Not a column or enum |
| Freshness timestamps | Not columns. `Job.updated_at` is the ORM row timestamp |
| `app/agents/jobs/` | Placeholder. Not a discovery agent |

`Job.status` allows `active` or `closed`. That status is not a freshness clock. See [Job catalog and freshness](../../architecture/data.md#job-catalog-and-freshness).

## Handoff snapshot (8 October 2026)

| | |
|--|--|
| Current status | Architecture **designed / decided**. Runtime **planned** |
| Implemented functionality | ORM tables for company, job, search intent, and match. No search behavior |
| Accepted decisions | [ADR 004](../../adr/004-catalog-first-job-search.md) |
| Open questions | The deferred list in [Job Search](../../architecture/job-search.md#intentionally-deferred-for-this-flow), including `SourceExecution`, queue technology, deduplication, freshness columns, and whether Job Search is later extracted. `Company` ownership across a future split is a separate open question in [Data architecture](../../architecture/data.md) |
| Files | `app/db/models/catalog.py`, `app/db/models/search.py`, `app/db/models/enums.py`, `alembic/versions/244a3d756668_initial_schema.py`, `tests/test_db_models.py`. No workflow |
| Tests | ORM metadata only. No database connection and no search scenario |
| Known limitations | Creating a `JobSearchRequest` is not possible through the CLI. Matches are never computed |
| Next recommended step | Leave Job Search unimplemented while Profile Reconciliation is still in design. Do not add `SearchExecution` in an ingestion change |
