"""Shared detection logic for blocking AI-agent access to .env secret files.

Used by the Claude Code PreToolUse hook (.claude/hooks/protect-env.py) and
the Cursor hooks (.cursor/hooks/before_read_file.py,
.cursor/hooks/before_shell_execution.py). Kept deliberately simple: this
blocks standard, recognizable access patterns, not every possible
obfuscation of them.
"""

import re

ALLOWED_EXACT_NAMES = {".env.example", ".env.sample", ".env.template"}

# Splits a raw shell command into word-like tokens on whitespace and the
# usual shell metacharacters, so a filename is caught whether it's a bare
# argument, inside a pipeline, or inside unescaped quotes.
_TOKEN_RE = re.compile(r"""[^\s"'<>|&;()]+""")

def is_protected_name(name: str) -> bool:
    """True for '.env' and '.env.<anything>' (incl. wildcard forms like
    '.env*'), except the explicitly allowed example/sample/template files."""
    if name in ALLOWED_EXACT_NAMES:
        return False
    if name == ".env" or name.startswith(".env."):
        return True
    if name.startswith(".env") and len(name) > 4 and name[4] in "*?[":
        return True
    return False


def is_protected_path(path_str: str) -> bool:
    if not path_str:
        return False
    normalized = path_str.replace("\\", "/").rstrip("/")
    name = normalized.rsplit("/", 1)[-1]
    return is_protected_name(name)


def _basename(token: str) -> str:
    return token.replace("\\", "/").rsplit("/", 1)[-1]


def command_touches_protected(command: str):
    """Returns (blocked: bool, reason: str) for a raw shell command string."""
    if not command:
        return False, ""

    tokens = _TOKEN_RE.findall(command)

    for token in tokens:
        name = _basename(token)
        if is_protected_name(name):
            return True, f"command references protected secrets file '{name}'"

    return False, ""
