---
name: career-ai-workflow
description: >-
  Guides Career AI work from repository context through requirements, guided
  system design, decision checkpoints, incremental implementation plans,
  approved edits, diff review, documentation, and feature handoff. Use when
  the user asks to start a new feature, continue an existing feature, review
  project status, plan implementation, review architecture, review database
  design, prepare a Cursor implementation task, review implementation changes,
  update project documentation, prepare a feature handoff, or close a feature.
  The same workflows apply when the user asks for them in Hebrew.
---

# Career AI workflow

This file is the procedure for feature work. Project facts and accepted decisions stay in the repository docs. Do not paste those docs into chat or into this skill.

Canonical copy: `.cursor/skills/career-ai-workflow/SKILL.md`. `.claude/skills/career-ai-workflow` is a symlink to that directory. Edit the canonical file only.

## Invocation

Apply this skill when the request matches the description. The user can also attach it explicitly:

- Cursor: `/career-ai-workflow`. Custom Mode (Option+Enter) keeps it for the session. Automatic selection is separate from that slash invocation.
- Claude Code: `/career-ai-workflow`. Claude may also load the skill when the description matches. That automatic load is not the same mechanism as Cursor.

Do not assume both tools activated the skill. If the task is one of the triggers above and this skill is not already in context, read this file and follow it.

## Context discovery

The user does not need to name files. Discover context from the repository. Read progressively. Stop when the open question is answered. Do not read the whole tree.

1. `AGENTS.md`
2. `docs/project-management/README.md` (entry point, status vocabulary, links)
3. `docs/project-management/project-status.md`
4. The feature page for this task. List `docs/project-management/features/` and open only the pages the request, the project-management README, the status page, or `docs/project-management/roadmap.md` point to. If none match, say so and ask which feature.
5. Architecture, ADR, design, and flow pages linked from that feature page and from `docs/project-management/README.md`. Read `docs/adr/` records that the feature or the decision register cites. Do not open every ADR by default.
6. `docs/project-management/decision-register.md` when the task touches a decision, an open question, or a possible disagreement between records.
7. `docs/project-management/working-agreement.md` for process, design conversations, and handoff. `docs/development/documentation.md` before editing docs.
8. Implementation, and only the area the docs identify: `app/`, then `tests/` and `alembic/` when behavior, persistence, or a schema claim is in play.

Authority, in this order:

- Application code, Alembic migrations, and tests: what is implemented.
- Accepted ADRs and accepted design pages: constraints on new architecture.
- `docs/project-management/`: progress, decisions, and open questions. Not a substitute for the technical docs or the code.

Do not treat a documented plan as implemented behavior. If a page and the code disagree, follow [Contradictions](#contradictions).

## Status labels

Use the labels defined in `docs/project-management/README.md`:

| Say | Label |
|-----|--------|
| Implemented | **Implemented** |
| Decided | **Designed / decided** |
| In design | **In design** |
| Planned | **Planned** |
| Deferred | **Future / deferred** |

A mapped table can be **Implemented** while the workflow that writes it is still **Planned**. Say which one is true. Do not invent a status the docs and the code do not support.

## Feature sequence

Move one step at a time. Do the step the user asked for. Do not implement during requirements or design. Do not skip a decision that is still open.

1. Requirements
2. Guided system design
3. Decision checkpoint
4. Incremental implementation plan
5. Implementation
6. Diff review and validation
7. Documentation update
8. Feature handoff

Commit and pull request are not an automatic next step. They happen only when the user explicitly asks, on a feature branch. See [Safety](#safety-and-approval).

### 1. Requirements

Clarify only what is still unknown:

- user-facing behavior
- functional and non-functional requirements
- scope and out of scope
- edge cases
- acceptance criteria

Ask only the questions that change the design or the scope. Check the feature page and the decision register before asking something the repository already answered.

### 2. Guided system design

The user is learning system design by building this product. Do not open with a finished architecture.

Present the meaningful alternatives for the decision at hand. Ask the user to reason about the trade-off. Prefer one design question at a time.

Explain only the concepts this feature forces a choice on: relationships and cardinality, data modeling, consistency, persistence, separation of concerns, security, performance, reliability, scalability. Tie each explanation to this feature. Skip theory the feature does not need.

Do not choose an open architectural option on the user's behalf. Do not add queues, workers, a second service, LangGraph, a model router, or an evaluation platform unless a recorded decision says the current requirement needs it (`AGENTS.md`).

### 3. Decision checkpoint

After the user accepts a decision, record it before later work depends on chat memory:

- why this option was chosen
- alternatives considered, when they mattered
- components affected
- the owning page: an ADR when reversal is expensive (`docs/development/documentation.md`), otherwise the architecture or design page that already owns the topic
- a row in `docs/project-management/decision-register.md` that points at that page

The register does not itself accept a decision or close an open question. Leave unresolved questions open. Do not mark an unresolved discrepancy as accepted.

### 4. Incremental implementation plan

Break the approved scope into small steps that can be reviewed on their own. For each step:

- goal
- files likely affected
- expected behavior
- tests
- acceptance criteria

Do not plan an entire complex feature as one pass. Stop after the plan and wait for approval before editing, unless the user already approved that scope.

### 5. Implementation

Before editing:

- `git status` and `git branch --show-current`
- confirm the scope the user approved
- re-read `AGENTS.md` and the feature page if this is a new session
- leave unrelated uncommitted work untouched

Do not switch branches, discard changes, or run destructive Git commands unless the user authorizes that operation. Implement only the approved step. A generated diff is not approval.

Cursor is the default environment for repository edits (`docs/project-management/working-agreement.md`). Claude Code edits the repository only when the user assigns that task in the current conversation. Do not rewrite the working agreement to widen that rule unless the user asks.

### 6. Diff review and validation

After edits:

- read the diff and separate intended edits from unrelated ones
- run the tests that cover the change
- for application code, also run `uv run ruff check app tests alembic`
- for a docs navigation or content change, run `uv run mkdocs build`
- check the feature page and the technical page still agree
- report limitations and any check that did not run

State that a check passed only after that command exits successfully in this session.

### 7. Documentation update

Update the feature page and the technical page that owns the change, in the same change, when behavior, contracts, configuration, or architecture change. Follow `docs/development/documentation.md`.

Link to the authoritative page. Do not copy it into a second file. Keep status labels accurate. Add a new docs page to `mkdocs.yml` `nav` in that same change. Skip docs for trivial edits, formatting-only changes, behavior-preserving refactors, and test-only internals.

### 8. Feature handoff

Before ending the feature, or before the work moves to another conversation, write a handoff a new session can use without this chat. Put it on the feature page under `docs/project-management/features/`. Link technical pages. Do not paste them.

Record:

- current feature status, using the labels above
- what was implemented
- accepted decisions
- files changed
- tests executed, including commands that were not run
- known limitations
- open questions
- next step

## Tool responsibilities

| Tool | Responsibility |
|------|----------------|
| ChatGPT | Requirements, guided system design, architecture discussion, decisions with the user, and a focused implementation prompt |
| Cursor | Repository edits, tests, documentation updates, and diff review |
| Claude Code | The same engineering rules. Only the task explicitly assigned in this conversation. Same design and approval boundaries |
| Git | Feature branches, reviewable commits, and pull requests. History stays in the repository |

Do not treat model output as accepted design or as approved code. If a decision is still open, stop and ask. Do not implement one of the options to "unblock" the work.

## Safety and approval

Reading and searching the repository does not need extra approval.

Do not:

- print, copy, or commit secrets, or paste `.env` into docs, logs, or chat. Variable names live in `.env.example` and `docs/development/config.md`
- treat `examples/` or illustrative profiles as the user's personal data
- commit, push, or change `main` unless the user explicitly asks
- run destructive Git commands unless the user authorizes that command
- refactor code outside the approved scope
- add a migration, change a schema, or mutate a production database without explicit approval
- implement an unresolved design decision
- report a test result or an implementation status that was not established in this session

Explicit user approval is required before:

- a significant architectural change
- a database schema change
- a destructive operation
- a production data change
- commit or push
- expanding the agreed scope

## Communication

Communicate with the user primarily in Hebrew. Keep English for code, technical identifiers, file paths, commands, commit messages, skill metadata, and repository documentation.

Repository documentation and AI instructions are written in English. That includes this skill. See `AGENTS.md` and `docs/project-management/working-agreement.md`.

Be concise and technically precise. One design question at a time. When several alternatives exist, keep only the ones that change this decision.

When reporting progress, use the status labels above so **Implemented**, **Designed / decided**, **In design**, **Planned**, and **Future / deferred** stay distinct.

## Contradictions

When two sources disagree:

1. Name both sources.
2. State the conflict.
3. Check whether one source is older or already marked open in the decision register.
4. If it is still unresolved, ask the user. Do not pick a winner.
5. Do not silently rewrite an accepted ADR, the working agreement, or an accepted design rule. A change to those is its own decision.

Known open disagreements stay listed in `docs/project-management/decision-register.md`. Surface them. Do not close them inside an unrelated edit.
