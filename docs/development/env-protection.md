# Protecting `.env` from AI coding agents

Blocks Claude Code and Cursor from reading, editing, writing, or
shell-accessing `.env`/`.env.*` files at any depth. Exceptions:
`.env.example`, `.env.sample`, `.env.template` stay readable.

## Layers

| Tool | Layer | File |
|------|-------|------|
| Claude Code | Permission deny rules (exact `.env` only - deny rules can't carve out exceptions, so `.env.*` is left to the hook) | `.claude/settings.json` |
| Claude Code | `PreToolUse` hook, matches `Read\|Edit\|Write\|MultiEdit\|Grep\|Glob\|Bash` | `.claude/hooks/protect-env.py` |
| Cursor | `.cursorignore` - primary layer; the only one that survives a file already open in the editor | `.cursorignore` |
| Cursor | `beforeReadFile` / `beforeShellExecution` hooks | `.cursor/hooks.json`, `.cursor/hooks/before_read_file.py`, `.cursor/hooks/before_shell_execution.py` |

All three Python hook scripts import shared detection from
`scripts/env_guard/common.py`.

Each hook command tries `python3` first and falls back to `python` via an
explicit `if/else`, since which name is on `PATH` varies by machine - this
has to preserve the hook's exit code exactly, so it's not written as a
`&&`/`||` chain (see `tests/test_env_guard.py::test_configured_*` for the
regression on that).

## What the detection actually checks

`scripts/env_guard/common.py` only flags a **direct, literal reference**
to a protected filename - as a bare argument (`cat .env`) or as an
`--opt=value` form (`--file=.env`). It does not parse shell semantics
(pipes, combined flags, multiple search operands) or try to predict what
an unscoped `grep -r`/`rg` over a directory might return.

That's a deliberate scope decision, not an oversight: this is a
best-effort guard against ordinary/accidental access, not a hard security
boundary - it's also trivially bypassed by e.g. building the filename via
string concatenation instead of writing it literally. An earlier version
tried to also catch unscoped recursive searches by walking the search
directory for protected files, but each added layer of shell-parsing
precision (multi-operand paths, pipelines, combined flags) introduced its
own bugs, so it was reverted in favor of keeping the detection simple and
correct for the common case.

## Tests

`tests/test_env_guard.py` covers the filename-matching rules and the
command-reference checks, plus three end-to-end tests that run the
*actual configured* `settings.json`/`hooks.json` command strings through
`bash -c` (skipped if `bash` isn't on `PATH`) and assert the real exit
code / JSON permission value - not just the Python script in isolation.

## After changing any of this

Restart Claude Code and Cursor - both read their hook/permission config
at startup, not per request.
