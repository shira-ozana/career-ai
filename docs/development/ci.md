# Continuous integration

GitHub Actions runs the checks in `.github/workflows/ci.yml`.

## When it runs

- Every push to any branch
- Pull requests that target any branch
- Manual runs (`workflow_dispatch`)

There are no branch or path filters. Every run executes `tests`, `lint`, and `docs`. One failure does not cancel the others. Each check has a 10-minute limit.

A push to a branch that already has an open pull request starts both a push run and a pull-request run. Each of those runs executes all three checks.

This workflow does not change branch protection and does not require pull requests on personal development branches.

## Environment

Each check uses an Ubuntu runner, Python 3.13, and uv. The workflow token can read repository contents. It does not receive secrets, call a model provider, connect to a database, or deploy.

Dependencies are installed from the lockfile:

```bash
uv sync --locked --extra dev --extra docs
```

## Checks

| Check | Command |
|-------|---------|
| `tests` | `uv run --no-sync pytest -q` |
| `lint` | `uv run --no-sync ruff check app tests alembic scripts .claude/hooks .cursor/hooks` |
| `docs` | `uv run --no-sync mkdocs build --strict` |

Run the same commands locally before opening a pull request. Pytest and Ruff details are in [Testing](testing.md).

After these checks have completed on GitHub, repository settings can require the status checks named `tests`, `lint`, and `docs`. That requirement is not part of the workflow file.
