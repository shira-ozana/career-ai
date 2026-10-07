"""Shared detection logic for blocking AI-agent access to .env secret files.

Used by the Claude Code PreToolUse hook (.claude/hooks/protect-env.py) and
the Cursor hooks (.cursor/hooks/before_read_file.py,
.cursor/hooks/before_shell_execution.py).

Deliberately simple: this checks for a direct, literal reference to a
protected filename in a tool call or shell command. It does not try to
parse shell semantics (pipes, combined flags, multiple search operands) or
predict what a directory-wide search might turn up - that's a losing game
against an arbitrarily clever command line, and this guard is a speed bump
for ordinary usage, not a hard security boundary. See the project's PR
description for the known gaps this implies.
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


def _token_is_protected_reference(token: str):
    name = _basename(token)
    if is_protected_name(name):
        return name
    # Catches option-value forms like --file=.env or KEY=.env, where the
    # whole token isn't a bare filename but contains one after '='.
    if "=" in token:
        _, _, value = token.partition("=")
        value_name = _basename(value)
        if is_protected_name(value_name):
            return value_name
    return None


def command_touches_protected(command: str):
    """Returns (blocked: bool, reason: str) for a raw shell command string.
    Only checks for a direct, literal reference to a protected filename
    (as a bare argument or as an --opt=value); does not reason about what
    a recursive/unscoped search might otherwise return."""
    if not command:
        return False, ""

    for token in _TOKEN_RE.findall(command):
        name = _token_is_protected_reference(token)
        if name:
            return True, f"command references protected secrets file '{name}'"

    return False, ""
