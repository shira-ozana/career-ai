"""Shared detection logic for blocking AI-agent access to .env secret files.

Used by the Claude Code PreToolUse hook (.claude/hooks/protect-env.py) and
the Cursor hooks (.cursor/hooks/before_read_file.py,
.cursor/hooks/before_shell_execution.py).
"""

import os
import re

ALLOWED_EXACT_NAMES = {".env.example", ".env.sample", ".env.template"}

# Splits a raw shell command into word-like tokens on whitespace and the
# usual shell metacharacters, so a filename is caught whether it's a bare
# argument, inside a pipeline, or inside unescaped quotes.
_TOKEN_RE = re.compile(r"""[^\s"'<>|&;()]+""")

_SKIP_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv", "venv",
    ".mypy_cache", ".pytest_cache", ".ruff_cache", "dist", "build", ".next",
}

_RECURSIVE_GREP_CMDS = {"grep", "egrep", "fgrep"}
_RECURSIVE_GREP_FLAGS = {"-r", "-R", "--recursive"}
_RIPGREP_CMDS = {"rg", "ripgrep"}


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


def find_protected_files(directory: str, limit: int = 1):
    """List (never read) protected filenames found under `directory`."""
    found = []
    if not directory or not os.path.isdir(directory):
        return found
    for root, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if d not in _SKIP_DIRS]
        for fname in files:
            if is_protected_name(fname):
                found.append(os.path.relpath(os.path.join(root, fname), directory))
                if len(found) >= limit:
                    return found
    return found


def _resolve(path: str, cwd: str) -> str:
    if not path:
        return cwd or "."
    if os.path.isabs(path):
        return path
    return os.path.join(cwd or ".", path)


def directory_search_exposes_protected(path: str, cwd: str) -> str:
    """Returns the relative path of a protected file found under `path`
    (resolved against `cwd`), or '' if there is none or it's not a
    directory. Used for content-reading searches (e.g. Grep, grep -r, rg),
    where a directory-wide scope can surface secrets even though no single
    argument names a protected file directly."""
    hits = find_protected_files(_resolve(path, cwd), limit=1)
    return hits[0] if hits else ""


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


def _looks_like_recursive_search(tokens) -> bool:
    lowered = {t.lower() for t in tokens}
    if lowered & _RIPGREP_CMDS:
        return True
    if lowered & _RECURSIVE_GREP_CMDS and (set(tokens) & _RECURSIVE_GREP_FLAGS):
        return True
    return False


def _guess_search_target(tokens):
    skip_cmds = _RECURSIVE_GREP_CMDS | _RIPGREP_CMDS
    candidates = [t for t in tokens if not t.startswith("-") and t.lower() not in skip_cmds]
    return candidates[-1] if candidates else "."


def command_touches_protected(command: str, cwd: str = None):
    """Returns (blocked: bool, reason: str) for a raw shell command string."""
    if not command:
        return False, ""

    tokens = _TOKEN_RE.findall(command)

    for token in tokens:
        name = _token_is_protected_reference(token)
        if name:
            return True, f"command references protected secrets file '{name}'"

    if _looks_like_recursive_search(tokens):
        target = _guess_search_target(tokens)
        hit = directory_search_exposes_protected(target, cwd)
        if hit:
            return True, f"recursive search over a directory containing a protected secrets file ({hit})"

    return False, ""
