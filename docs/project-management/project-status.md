# Project status

Snapshot from repository inspection on 8 October 2026. Status labels are defined in [Project management](README.md).

The running application is a CLI. It can analyze an already-structured profile and extract facts from text sources. PostgreSQL mappings and one Alembic revision exist. Neither CLI command reads or writes those tables.

## What runs today

| Area | Status | Evidence |
|------|--------|----------|
| Profile Analyzer CLI (`analyze-profile`) | **Implemented** | `app/cli.py`, `app/agents/profile/agent.py`, `app/models/profile.py` |
| Text profile extraction CLI (`extract-profile`) | **Implemented** | `app/workflows/profile_ingestion.py`, `app/agents/profile/extraction.py` |
| OpenAI structured client | **Implemented** | `app/tools/llm.py` (`StructuredLLM`, Responses API `responses.parse`) |
| Cursor SDK provider for extraction | **Implemented** | `app/tools/cursor_llm.py`. Optional. `extract-profile --provider cursor` |
| Deterministic mock LLM | **Implemented** | `app/tools/mock_llm.py`. Tests and `--mock` |
| PostgreSQL schema | **Implemented** as mappings and migration `244a3d756668_initial_schema` | `app/db/models/`, `alembic/versions/` |
| Wiring either CLI flow to the database | **Not implemented** | `ProfileIngestionFlow.run` returns JSON. No repository package |
| HTTP API | **Future / deferred** | `app/api/` is a placeholder docstring |
| LinkedIn, resume, and jobs agents | **Planned** placeholders | `app/agents/linkedin/`, `resume/`, `jobs/` |
| GitHub Actions CI | **Implemented** | `.github/workflows/ci.yml` runs tests, Ruff, and `mkdocs build --strict` |
| Authentication and authorization flows | **Not implemented** | `User` and `AuthIdentity` tables exist. No login or permission checks |
| Profile reconciliation and human review | **In design** | No review models, tables, or workflow engine |
| Job discovery and matching runtime | **Planned** | Tables exist. No search or scoring code |
| CV generation | **Planned** | `ResumeVersion` table exists. No tailoring flow |

Technical detail: [Architecture overview](../architecture/overview.md), [Future architecture](../architecture/future-architecture.md#current-next-and-future).

## Technology in this repository

`pyproject.toml` requires Python 3.13+. CI uses Python 3.13. The package manager is uv. Locked versions below are from `uv.lock` at the time of this snapshot. Minimum bounds are in `pyproject.toml`.

| Dependency | Locked version | Role |
|------------|----------------|------|
| pydantic | 2.13.4 | Contracts and settings models |
| pydantic-settings | 2.14.2 | `Settings` from the environment |
| openai | 2.48.0 | OpenAI Responses API client |
| cursor-sdk | 1.0.32 | Optional extraction provider |
| sqlalchemy | 2.0.52 | ORM |
| psycopg | 3.3.5 | PostgreSQL driver |
| alembic | 1.19.2 | Migrations |
| python-dotenv | 1.2.2 | Env file loading |
| pytest | 9.1.1 | Tests (dev) |
| pytest-asyncio | 1.4.0 | Async tests (dev) |
| ruff | 0.16.0 | Lint (dev) |
| mkdocs | 1.6.1 | Docs site (docs extra) |
| mkdocs-material | 9.7.7 | Docs theme (docs extra) |

LangGraph, a queue library, Redis, and a web framework are not dependencies.

Settings and secret variable names: [Config and secrets](../development/config.md). Local values stay in `.env`.

## Database entities that exist

Mapped tables, and only these, are asserted in `tests/test_db_models.py`:

`users`, `auth_identities`, `candidate_profiles`, `companies`, `experiences`, `skills`, `candidate_profile_skills`, `jobs`, `job_search_requests`, `job_matches`, `resume_versions`.

The same test asserts that `tailored_cvs`, `workflow_states`, `educations`, and `institutions` are absent.

Relationships and ownership rules: [Data architecture](../architecture/data.md). `SearchExecution`, `SourceExecution`, `ProfileSource`, `ProfileIngestionRun`, `ReviewItem`, and `ReviewDecision` are not mapped.

## Tests

Unit tests cover analyzer contracts, ingestion contracts, extraction sequencing, LLM provider adapters, ORM metadata, and database settings. They do not open PostgreSQL and they do not call OpenAI or Cursor. See [Testing](../development/testing.md).

A prior conversation reports two operational events:

- A manual `extract-profile --provider cursor` run with two text sources succeeded, and the output validated as `ExtractedCandidateProfile`.
- Live OpenAI calls hit provider quota errors.

This repository does not re-run those calls. A quota error is an account limit. It is not recorded as an application defect.

## Active design thread

Profile reconciliation is **in design**. Implementation has not started. Accepted rules and the questions that are still open are in [Profile reconciliation](features/profile-reconciliation.md).

One policy disagreement is unresolved: the architecture docs allow a non-conflicting new skill to merge without review, and the later design discussion requires user review before any new canonical fact is stored. See the [Decision register](decision-register.md#unresolved-discrepancies).
