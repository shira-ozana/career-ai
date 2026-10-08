# AGENTS.md

Instructions for coding assistants working in this repository.

Read the relevant docs before editing:

- [Architecture overview](docs/architecture/overview.md)
- [Data architecture](docs/architecture/data.md)
- [Future architecture](docs/architecture/future-architecture.md)
- ADRs in `docs/adr/`
- the feature page under `docs/project-management/features/`
- [Working agreement](docs/project-management/working-agreement.md)

Application code, Alembic migrations, and tests are the source of truth for what is implemented. Accepted ADRs are architectural constraints. Project-management pages record status and open questions. They do not replace the technical docs.

## Project workflow

For feature work — starting or continuing a feature, project status, system design, an implementation plan, architecture or database review, a Cursor implementation task, diff review, documentation updates, a feature handoff, or closing a feature — follow the `career-ai-workflow` skill. It is the procedure for how to work. This file and `docs/` stay the source of project facts and accepted decisions.

- Cursor: `.cursor/skills/career-ai-workflow/SKILL.md`, or `/career-ai-workflow`
- Claude Code: the same directory through `.claude/skills/career-ai-workflow`, or `/career-ai-workflow`

## Working in the repo

- Change only the files the task requires.
- Prefer a small diff that can be reviewed on its own.
- Do not add infrastructure (queues, workers, a second service, LangGraph, a model router, an evaluation platform) unless a recorded decision says the current requirement needs it.
- Keep **implemented**, **designed / decided**, **in design**, **planned**, and **future / deferred** distinct. Do not describe a planned type, table, or workflow as if the code already contains it.
- Do not silently resolve an open question in [Profile reconciliation](docs/project-management/features/profile-reconciliation.md) or the [Decision register](docs/project-management/decision-register.md). Surface it.
- If a change would revise an accepted ADR or an accepted design rule, stop and record that as an explicit decision. Do not fold the change into an unrelated edit.
- When behavior, contracts, configuration, or architecture change, update the matching docs in the same change. Follow [Documentation guidelines](docs/development/documentation.md). Update the feature page when the feature's status or limitations change.
- Run the relevant tests and `uv run ruff check app tests alembic` for code changes. For docs navigation or content changes, run `uv run mkdocs build`.
- Do not commit, push, or change `main` unless the user explicitly asks.

## Documentation language

Write repository documentation and AI instructions in English. That includes `docs/`, `AGENTS.md`, `CLAUDE.md`, and skill files.

Communicate with the user primarily in Hebrew. Keep English for code, technical identifiers, file paths, commands, and commit messages.

## Secrets and sample data

- Never print, copy, or commit secrets. `.env` is gitignored. Use `.env.example` and [Config and secrets](docs/development/config.md) for variable names only.
- Do not treat `examples/` or illustrative profiles in the docs as the user's personal information.
