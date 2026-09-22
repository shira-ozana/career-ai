# ADR 002: Modular monolith with extractable module boundaries

## Status

Accepted

## Context

Career AI is one Python backend and one PostgreSQL database. Job discovery is expected to become a heavy I/O workload (multiple external sources, rate limits, timeouts, concurrent execution, catalog refresh, normalization, deduplication). Profile management and ordinary CRUD do not share that profile.

Treating the current system as microservices would add operational cost, distributed transactions, and database-per-service splits before any module has earned independent deployment.

Collapsing all boundaries into a single undifferentiated codebase would make a later Job Search extraction expensive.

## Decision

Career AI uses a **modular monolith**.

Principle:

> Design boundaries as if modules may become services; deploy as a monolith until independent deployment is justified.

Do not describe the current system as microservices.

Keep:

- one deployable backend
- one PostgreSQL database
- SQLAlchemy and Alembic
- clear logical ownership of user/career state vs global catalog data

The strongest likely future extraction candidate is Job Search / Job Platform. Discovery and Matching stay separate responsibilities even if they first run in-process, and they should not be assumed to become the same future service.

`JobSearchRequest` (search intent) and personalized `JobMatch` ownership stay Career AI user state so search history can survive replacement or extraction of the Job Search implementation.

`Company` is shared by `Experience` and `Job`. Future service ownership of `Company` is unresolved; do not redesign it in this decision.

## Consequences

- Documentation and design talk about modules and contracts, not currently deployed services.
- Database-per-service, distributed transactions, and service-to-service auth are deferred until an extraction is justified.
- Transport-friendly contracts (`CandidateSearchContext` / `SearchExecutionRequest`) may start as in-process objects.
- Anonymous catalog search can later read the global Job Catalog without a `User` or persisted `JobSearchRequest`.
