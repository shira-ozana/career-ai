# Job matching

**Designed / decided** as a separate responsibility from discovery. The matching runtime is **not implemented**.

Design: [Discovery vs Matching](../../architecture/job-search.md#discovery-vs-matching) and [ADR 004](../../adr/004-catalog-first-job-search.md). Table shape: [Data architecture](../../architecture/data.md).

## What the schema stores

`JobMatch` is one `JobSearchRequest` paired with one `Job`. It is user-specific because the search request belongs to a `CandidateProfile`. The job itself is global catalog data.

Mapped columns include `match_score` (0 through 100), `match_reason`, and `status` (`pending` or `reviewed`). Uniqueness is one row per (`job_search_request_id`, `job_id`). A repeated search must not insert a second match only because the same job was seen again.

`JobMatch` does not store which execution first discovered the match. That pointer is **planned**. The column name is supposed to be chosen before a migration. Full N:M history between matches and executions is **deferred**.

Nothing in `app/` constructs a `JobMatch`. `app/agents/jobs/` is a placeholder and is not a matcher.

## Accepted matching direction

Matching consumes catalog `Job` rows plus candidate and search context. It does not score an uncatalogued provider payload.

The transport-friendly context discussed for a later split is `CandidateSearchContext` / `SearchExecutionRequest`. Those names are not Python types in the repository. Today they would be in-process objects if matching existed. ORM entities are not the cross-module contract. [ADR 003](../../adr/003-application-owns-workflows.md).

Personalized matching assumes an authenticated user, a profile, and a search request. Anonymous catalog browsing is a **future / deferred** extension and must not require `JobMatch`. It is not built.

Ranking policy, thresholds, and batching are not specified in code. [Future architecture](../../architecture/future-architecture.md#model-routing) lists `JOB_MATCHING` as a possible later task for model policy. There is no router.

## Handoff snapshot (8 October 2026)

| | |
|--|--|
| Current status | Table **implemented**. Scoring, ranking, and persistence of results **planned** |
| Implemented functionality | `JobMatch` mapping, uniqueness, score check constraint, optional link from `ResumeVersion` |
| Accepted decisions | Separate from discovery. One match per search request and job. First-discovered execution pointer planned, name not chosen |
| Open questions | Field name for first discovery. Whether N:M execution history is ever needed. Matching parallelism. How much of matching is deterministic filtering versus a model. Service extraction is deferred with Job Search |
| Files | `app/db/models/search.py`, `app/db/models/enums.py` (`JobMatchStatus`), `tests/test_db_models.py` |
| Tests | Metadata and constraints only |
| Known limitations | No scores are produced. `status` values `pending` and `reviewed` are not a review workflow |
| Next recommended step | Do not implement matching ahead of catalog-first discovery, and do not start either while reconciliation design is open |
