# ADR 003: Application layer owns workflows; agents are capabilities

## Status

Accepted

## Context

The implemented Profile Analyzer is a CLI-invoked agent with typed I/O and no persistence. Earlier target diagrams placed agents next to a data-access layer in a way that could be read as `API → Agent → database`.

Agents that own sequencing, transactions, authorization, and ORM access couple AI capabilities to application workflow. That makes testing, extraction, and authorization harder, and it encourages passing SQLAlchemy objects across module boundaries.

The next implementation milestone is Profile Ingestion: structured JSON persisted atomically through an application service and repository. That slice should set the ownership pattern for later Job Search.

## Decision

Agents are **capabilities**, not owners of application workflows.

Prefer:

```text
API / CLI
  → Application / Workflow
    → Domain / Application Service
      → Agent capability when needed
        → Repository
          → PostgreSQL
```

Avoid:

```text
API → Agent → direct DB access
```

The deterministic application layer owns sequencing, persistence, transactions, authorization, retries/status handling, and orchestration.

Agents use explicit input/output contracts. Do not pass SQLAlchemy ORM objects across module boundaries where a stable contract should exist.

Authentication (`AuthIdentity` → `User`) and authorization (what that actor may access) stay distinct. User-owned resources are only accessed or mutated in an authenticated actor context. Application services enforce ownership. Repositories are not the sole authorization layer.

Do not build a full RBAC system now. Do not model background workers or future service actors as human `User` rows.

## Consequences

- Profile Analyzer can remain a capability called by the CLI until a workflow needs it.
- Profile Ingestion introduces the first application service and repository; it does not give the analyzer unrestricted database access.
- Future Job Search uses application-owned `SearchExecution` lifecycle, with agents or providers invoked behind that service.
- HTTP API, when added, calls application services rather than agents directly.
