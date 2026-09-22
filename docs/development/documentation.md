# Documentation guidelines

Update docs in the **same PR / change** as the code whenever possible.

## When a code change needs docs

Update documentation if the change:

- Adds, removes, or relocates a module, agent, or interface
- Changes a public contract (CLI, models, config, env vars)
- Changes an end-to-end flow
- Introduces a non-obvious architectural choice

Skip a docs update for typo-level edits, refactors that do not change behavior, or test-only internals.

## Which folder to update

| Kind of change | Folder | Create the file if missing |
|----------------|--------|----------------------------|
| System shape, layers, package layout | `docs/architecture/` | `overview.md` or a focused page |
| Persistence, ingestion, domain data model | `docs/architecture/` | `data.md` |
| Job Search pipeline and search execution | `docs/architecture/` | `job-search.md` |
| A specific feature or component | `docs/design/` | `<component>.md` |
| A durable architectural decision | `docs/adr/` | `NNN-short-title.md` |
| An end-to-end user or system path | `docs/flows/` | `<flow-name>.md` |
| Setup, tooling, testing, conventions | `docs/development/` | a focused page |

Do not add empty placeholder pages. Add a file when there is something real to say.

If you add a new page, list it in `mkdocs.yml` `nav` in the same change.

When documenting target architecture, mark each topic as **implemented**, **decided**, **proposed**, **open question**, or **future consideration**. Do not describe unimplemented components as if they already exist in code.

## When to write an ADR

Create an ADR in `docs/adr/` when the decision is expensive to reverse or future contributors need the rationale, for example:

- Choosing or replacing an LLM provider or orchestration approach
- Changing how agents share state or contracts
- Introducing a new persistence or API boundary
- Choosing modular-monolith vs independently deployed services
- Changing whether agents or application services own workflows

Do not write an ADR for local implementation details that are obvious from the code.

Name files `NNN-short-title.md` (e.g. `001-structured-outputs.md`). Number from the highest existing ADR + 1.

## Preview and build

```bash
uv sync --extra dev --extra docs
uv run mkdocs serve    # local preview
uv run mkdocs build    # must succeed before merge
```
