# Working agreement

Career AI is developed as a real career-management product and as a way to practice Python, AI engineering, multi-agent design, backend development, database design, and System Design. The product is a usable system. It is not treated as a short demo that can ignore durability, review, or documentation.

Cursor is the only environment that modifies this repository. ChatGPT is used for requirements, design, technical learning, and implementation planning. The repository is the durable source of truth. Chat memory is supporting context.

## Project organization

There is an existing ChatGPT project named `career-ai`.

Conversations are split by responsibility:

| Conversation | Responsibility |
|--------------|----------------|
| 00 — Project Roadmap | Sequence, status, and what to work on next |
| 01 — System Architecture | Module boundaries, workflows, and cross-cutting design |
| 02 — Database Design | Schema, relationships, and persistence decisions |
| Feature — Profile Reconciliation | The active feature design |
| Infrastructure — GitHub & CI/CD | Repository hosting, checks, and collaboration |

Create another feature conversation only when that feature needs its own requirements and design thread. Do not return to one long conversation for every topic.

## Feature development process

Each feature follows this sequence:

1. **Requirements** — what the feature must do, and what it must leave unchanged.
2. **Guided System Design** — the user reasons through the design before a solution is recommended.
3. **Incremental Implementation Plan** — small repository changes, in an order that can be reviewed.
4. **Cursor Implementation** — Cursor applies the planned change in the repository.
5. **Diff Review and Tests** — review the diff and run the relevant tests and lint checks.
6. **Documentation Update** — update the technical docs and, when the checkpoint below applies, this section.
7. **Commit / PR** — feature branch and pull request. `main` is protected from uncontrolled changes.
8. **Feature Handoff** — record the snapshot described below before leaving the feature or the conversation.

## Guided System Design

The user is learning System Design. A design conversation should not open with a finished architecture.

Present meaningful engineering questions. Let the user work through trade-offs before recommending a solution. Explain concepts through decisions this project actually has to make.

Keep the discussion on:

- data modeling
- relationships and cardinality
- API design
- separation of concerns
- persistence
- consistency
- performance
- scalability
- reliability
- security
- trade-offs

Avoid premature optimization and infrastructure that the current feature does not need. Workers and queues do not, by themselves, mean microservices. See [ADR 002](../adr/002-modular-monolith.md) and [Future architecture](../architecture/future-architecture.md).

## Implementation principles

- Cursor performs repository modifications.
- ChatGPT provides design guidance and focused Cursor prompts.
- Work in small, reviewable changes.
- Review diffs.
- Run relevant tests.
- Do not let an assistant implement an entire complex feature in one unreviewed step.
- Do not silently change a previously accepted architectural decision. If two records disagree, document the disagreement and resolve it explicitly. See the [Decision register](decision-register.md).
- Keep implementation aligned with documentation.
- Use feature branches and pull requests.
- Keep `main` free of uncontrolled changes.
- Do not introduce LangGraph, a model router, queues, or a second service without a decision that says the current feature requires it.
- Do not resolve an open design question by implementing one of the options.

Accepted architectural constraints already live in the ADRs:

- [ADR 001: PostgreSQL](../adr/001-postgresql.md)
- [ADR 002: Modular monolith](../adr/002-modular-monolith.md)
- [ADR 003: Application-owned workflows](../adr/003-application-owns-workflows.md)
- [ADR 004: Catalog-first Job Search](../adr/004-catalog-first-job-search.md)

## Documentation language

Write repository documentation in English. That includes architecture, design, ADRs, flows, development guides, project-management pages, and assistant instruction files (`AGENTS.md`, `CLAUDE.md`, and skills).

Assistants communicate with the user primarily in Hebrew. English remains the language of repository text, code, technical identifiers, file paths, commands, and commit messages.

## Documentation checkpoints

### Decision checkpoint

After a significant architectural decision, update the repository before relying on chat memory:

- add or update an ADR when the decision is expensive to reverse ([Documentation guidelines](../development/documentation.md))
- update the architecture or design page that owns the topic
- add a row to the [Decision register](decision-register.md)
- leave questions that are still open marked as open

### Feature handoff

Before ending a feature, or before moving that work to another conversation, record:

- current status
- implemented functionality
- accepted decisions
- open questions
- files changed
- tests executed
- known limitations
- next recommended step

Put the durable copy in the feature page under `docs/project-management/features/`. Link to technical pages instead of pasting them.

The feature pages in this section are the handoff from the earlier single long conversation into this workflow. Later handoffs update those pages in the same change as the work they describe.

## What assistants must not treat as personal data

Files under `examples/` are sample payloads for the CLI. They are not a record of the user's real profile. Illustrative names, cities, titles, and skills in design discussions are examples of a rule, not biographical claims.
