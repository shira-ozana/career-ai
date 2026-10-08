#!/usr/bin/env python3
"""Cursor beforeReadFile hook: deny reads of .env secret files (exceptions:
.env.example, .env.sample, .env.template). See scripts/env_guard/common.py
for the shared detection logic also used by the Claude Code hook."""

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts" / "env_guard"))
from common import is_protected_path  # noqa: E402


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        print(json.dumps({"permission": "allow"}))
        return

    file_path = payload.get("file_path", "")

    if file_path and is_protected_path(file_path):
        print(json.dumps({
            "permission": "deny",
            "user_message": f"Blocked read of secrets file: {file_path}",
        }))
        return

    print(json.dumps({"permission": "allow"}))


if __name__ == "__main__":
    main()
