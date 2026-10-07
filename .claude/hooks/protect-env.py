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
from common import command_touches_protected, is_protected_path  # noqa: E402

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

    reason = None

    if tool_name in ("Read", "Write", "Edit", "MultiEdit", "NotebookEdit"):
        path = tool_input.get("file_path") or tool_input.get("notebook_path") or tool_input.get("path")
        if path and is_protected_path(path):
            reason = f"{tool_name} targets protected secrets file: {path}"

    elif tool_name in ("Glob", "Grep"):
        path = tool_input.get("path")
        pattern = tool_input.get("glob") or tool_input.get("pattern") or ""
        if path and is_protected_path(path):
            reason = f"{tool_name} path targets protected secrets file: {path}"
        elif pattern and is_protected_path(pattern):
            reason = f"{tool_name} pattern targets protected secrets file: {pattern}"

    elif tool_name == "Bash":
        command = tool_input.get("command", "")
        touched, why = command_touches_protected(command)
        if touched:
            reason = why

    if reason:
        print(f"BLOCKED by protect-env hook: {reason}\n{BLOCK_MESSAGE_SUFFIX}", file=sys.stderr)
        sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    main()
