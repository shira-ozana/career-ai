#!/usr/bin/env python3
"""Cursor beforeShellExecution hook: deny shell commands that touch .env
secret files (exceptions: .env.example, .env.sample, .env.template). See
scripts/env_guard/common.py for the shared detection logic also used by
the Claude Code hook."""

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts" / "env_guard"))
from common import command_touches_protected  # noqa: E402


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        print(json.dumps({"permission": "allow"}))
        return

    command = payload.get("command", "")
    touched, reason = command_touches_protected(command)

    if touched:
        print(json.dumps({
            "permission": "deny",
            "user_message": f"Blocked shell access to secrets file ({reason})",
            "agent_message": (
                "Access to .env secret files is blocked for AI agents in this project. "
                "Allowed exceptions: .env.example, .env.sample, .env.template."
            ),
        }))
        return

    print(json.dumps({"permission": "allow"}))


if __name__ == "__main__":
    main()
