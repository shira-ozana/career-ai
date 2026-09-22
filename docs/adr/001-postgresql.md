# ADR 001: PostgreSQL with SQLAlchemy

## Status

Accepted

## Context

Career AI persists a career-domain graph: users, canonical candidate profiles, experiences, reusable companies and skills, a system-level job catalog, job-search requests, matches, and resume versions.

The original evaluation was between a relational/PostgreSQL-style store and a MongoDB/document store. A Candidate Profile can look like a nested document, which made a document model tempting early on.

As the model solidified, the important operations became cross-entity: uniqueness and foreign keys, filtering and sorting matches, joining search intent to jobs and companies, and reusing Company and Skill identities.

A hosted PostgreSQL database (currently Supabase) is available for development. The application should not depend on vendor-specific database APIs. Career AI is a modular monolith: one PostgreSQL database for the whole backend until an extraction is justified. See [ADR 002](002-modular-monolith.md).

## Decision

Use **PostgreSQL** as the primary relational database, accessed with **SQLAlchemy 2.x** and **psycopg 3**, with **Alembic** for migrations.

Supabase is the current **hosting provider** for PostgreSQL. It is not an application database API. Auth, storage, and other Supabase products are separate future decisions.

## Consequences

- Schema, constraints, and relationships are explicit and migratable.
- The ORM layer talks SQLAlchemy/PostgreSQL URLs (`postgresql+psycopg://...`), not a Supabase SDK.
- JSONB can still be added later for selectively flexible fields; it is not required now.
- Switching away from PostgreSQL later would be expensive because of constraints, migrations, and SQLAlchemy mappings.
