# ADR 004: Catalog-first Job Search with SearchExecution

## Status

Accepted

## Context

The schema already has `Job` (global catalog), `JobSearchRequest` (intent), and `JobMatch` (unique per request + job). It does not distinguish a persistent search from a single run, job **status** from job **freshness**, or Discovery from Matching.

If every search started from external sources, Career AI would skip its own catalog, duplicate jobs outside that catalog, and lose a stable identity for matching and later CV tailoring.

If Discovery and Matching were designed as one blob, a later extraction of the I/O-heavy Job Platform would drag AI matching with it, or vice versa.

## Decision

1. **`JobSearchRequest` is user-owned search intent.** It is not a search-engine execution. Search history stays in Career AI user state.

2. **`SearchExecution` is one run of that request** (`JobSearchRequest` 1:N `SearchExecution`). Conceptual lifecycle: `PENDING` → `RUNNING` → `COMPLETED` | `PARTIAL` | `FAILED`. Persistence is planned, not in the current schema.

3. **The internal Job Catalog always participates first.** External discovery enriches and refreshes that catalog. It does not create a separate temporary job universe.

4. **Discovery and Matching are separate responsibilities**, even inside the monolith. Discovery is primarily I/O. Matching may become AI/compute-heavy.

5. **`JobMatch` uniqueness remains one row per (`JobSearchRequest`, `Job`).** Repeated executions must not duplicate matches. Architecture preserves a first-discovered execution pointer; exact column name is chosen before migration. Full N:M history is deferred.

6. **Job status and Job freshness are different.** Freshness metadata is required conceptually (`first_seen_at` / `last_seen_at` / `last_verified_at` are examples only). Exact columns and TTL are deferred. Targeted per-job verification must be possible without rerunning an entire search.

7. **Heavy search execution is asynchronous.** The synchronous path only validates, creates/reads the request, creates a `SearchExecution`, starts work, and returns identifiers and status. Queue technology is deferred. A single provider failure may yield `PARTIAL` rather than `FAILED`.

8. **External source policy** is conceptually `AUTO` (default) or `SELECTED`. The catalog always participates. "No external source selected" must not mean search nowhere. Do not add policy columns until Job Search flow design. Avoid omitted-vs-empty array ambiguity.

9. **`SourceExecution` persistence is deferred** until the detailed Job Search flow is designed.

## Consequences

- Profile Ingestion does not add search tables or freshness columns.
- The implemented ERD stays as-is until Job Search implementation.
- Anonymous catalog search can later query `Job` without `User` / `JobSearchRequest` / `JobMatch`.
- Matching consumes catalog jobs plus a transport-friendly `CandidateSearchContext` / `SearchExecutionRequest`.
