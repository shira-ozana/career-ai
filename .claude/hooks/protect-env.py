#!/usr/bin/env python3
"""Claude Code PreToolUse hook: block reads/edits/writes/searches/shell
commands that touch .env secret files (exceptions: .env.example,
.env.sample, .env.template). See scripts/env_guard/common.py for the
shared detection logic also used by the Cursor hooks."""

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts" / "env_guard"))
from common import command_touches_protected, directory_search_exposes_protected, is_protected_path  # noqa: E402

BLOCK_MESSAGE_SUFFIX = (
    "Access to .env secret files is blocked for AI agents in this project. "
    "Allowed exceptions: .env.example, .env.sample, .env.template."
)


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    tool_name = payload.get("tool_name", "")
    tool_input = payload.get("tool_input") or {}
    cwd = payload.get("cwd") or str(PROJECT_ROOT)

    reason = None

    if tool_name in ("Read", "Write", "Edit", "MultiEdit", "NotebookEdit"):
        path = tool_input.get("file_path") or tool_input.get("notebook_path") or tool_input.get("path")
        if path and is_protected_path(path):
            reason = f"{tool_name} targets protected secrets file: {path}"

    elif tool_name == "Glob":
        # Glob only returns matching filenames, never file content, so it's
        # enough to check the explicit path/pattern rather than walking the
        # whole search directory.
        path = tool_input.get("path")
        pattern = tool_input.get("pattern") or ""
        if path and is_protected_path(path):
            reason = f"Glob path targets protected secrets file: {path}"
        elif pattern and is_protected_path(pattern):
            reason = f"Glob pattern targets protected secrets file: {pattern}"

    elif tool_name == "Grep":
        # Grep reads file content, so a directory-wide search can surface a
        # secret's value even when no argument names it directly.
        path = tool_input.get("path")
        glob_arg = tool_input.get("glob") or ""
        if path and is_protected_path(path):
            reason = f"Grep path targets protected secrets file: {path}"
        elif glob_arg and is_protected_path(glob_arg):
            reason = f"Grep glob filter targets protected secrets file: {glob_arg}"
        else:
            hit = directory_search_exposes_protected(path, cwd)
            if hit:
                reason = f"Grep search scope contains a protected secrets file ({hit})"

    elif tool_name == "Bash":
        command = tool_input.get("command", "")
        touched, why = command_touches_protected(command, cwd)
        if touched:
            reason = why

    if reason:
        print(f"BLOCKED by protect-env hook: {reason}\n{BLOCK_MESSAGE_SUFFIX}", file=sys.stderr)
        sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    main()
