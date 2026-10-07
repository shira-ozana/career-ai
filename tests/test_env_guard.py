"""Regression tests for scripts/env_guard/common.py, the shared detection
logic behind the Claude Code and Cursor .env-protection hooks.

No real secrets are used or read anywhere in this file; all fixtures are
synthetic.
"""

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts" / "env_guard"))

from common import command_touches_protected, is_protected_name, is_protected_path  # noqa: E402

DOTENV = "." + "env"  # avoid a literal match for this repo's own Bash hook
EXAMPLE = DOTENV + ".example"
PRODUCTION = DOTENV + ".production"


def test_bare_env_is_protected():
    assert is_protected_name(DOTENV) is True


def test_env_suffix_variants_are_protected():
    assert is_protected_name(PRODUCTION) is True
    assert is_protected_name(DOTENV + "*") is True


def test_allowed_exceptions_are_not_protected():
    assert is_protected_name(EXAMPLE) is False
    assert is_protected_name(DOTENV + ".sample") is False
    assert is_protected_name(DOTENV + ".template") is False


def test_unrelated_dotfile_is_not_protected():
    assert is_protected_name(".environment") is False
    assert is_protected_name(".envrc") is False


def test_is_protected_path_checks_basename_at_any_depth():
    assert is_protected_path(f"a/b/c/{DOTENV}") is True
    assert is_protected_path(f"a/b/c/{EXAMPLE}") is False


def test_bash_direct_reference_is_blocked():
    blocked, _ = command_touches_protected(f"cat {DOTENV}")
    assert blocked is True


def test_bash_direct_reference_nested_is_blocked():
    blocked, _ = command_touches_protected(f"sed -n 1p config/{DOTENV}")
    assert blocked is True


def test_bash_allowed_exception_is_not_blocked():
    blocked, _ = command_touches_protected(f"cat {EXAMPLE}")
    assert blocked is False


def test_bash_unrelated_command_is_not_blocked():
    blocked, _ = command_touches_protected("ls -la src")
    assert blocked is False


def test_bash_ordinary_recursive_grep_is_not_blocked():
    # By design: this guard only catches a direct, literal reference to a
    # protected filename. It does not try to reason about what a
    # recursive/unscoped search might otherwise return (that's a losing
    # game against an arbitrarily clever command line) - documented as a
    # known limitation rather than chased with more parsing.
    blocked, _ = command_touches_protected("grep -r SECRET_KEY .")
    assert blocked is False


def test_option_value_form_root_is_blocked():
    # e.g. `dotenv --file=.env list`
    blocked, reason = command_touches_protected(f"dotenv --file={DOTENV} list")
    assert blocked is True
    assert DOTENV in reason


def test_option_value_form_nested_is_blocked():
    blocked, _ = command_touches_protected(f"dotenv --file=config/{DOTENV} list")
    assert blocked is True


def test_option_value_form_allowed_exception_is_not_blocked():
    blocked, _ = command_touches_protected(f"dotenv --file={EXAMPLE} list")
    assert blocked is False


# --- End-to-end: the actual configured shell command string, not just the
# Python script directly. Requires a POSIX shell (bash); skipped otherwise
# (e.g. on a bare Windows runner without git-bash on PATH).

_BASH = shutil.which("bash")


def _run_configured_command(command: str, payload: dict, cwd: Path):
    import os

    full_env = {**os.environ, "CLAUDE_PROJECT_DIR": str(ROOT)}
    return subprocess.run(
        ["bash", "-c", command],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        cwd=str(cwd),
        env=full_env,
    )


@pytest.mark.skipif(_BASH is None, reason="requires a POSIX shell (bash) on PATH")
def test_configured_claude_command_preserves_block_exit_code(tmp_path):
    settings = json.loads((ROOT / ".claude" / "settings.json").read_text())
    command = settings["hooks"]["PreToolUse"][0]["hooks"][0]["command"]
    payload = {"tool_name": "Read", "tool_input": {"file_path": f"{tmp_path}/{DOTENV}"}}
    proc = _run_configured_command(command, payload, cwd=ROOT)
    assert proc.returncode == 2, proc.stderr


@pytest.mark.skipif(_BASH is None, reason="requires a POSIX shell (bash) on PATH")
def test_configured_claude_command_allows_unrelated_file():
    settings = json.loads((ROOT / ".claude" / "settings.json").read_text())
    command = settings["hooks"]["PreToolUse"][0]["hooks"][0]["command"]
    payload = {"tool_name": "Read", "tool_input": {"file_path": "README.md"}}
    proc = _run_configured_command(command, payload, cwd=ROOT)
    assert proc.returncode == 0, proc.stderr


@pytest.mark.skipif(_BASH is None, reason="requires a POSIX shell (bash) on PATH")
def test_configured_cursor_shell_command_denies_blocked_payload():
    hooks_cfg = json.loads((ROOT / ".cursor" / "hooks.json").read_text())
    command = hooks_cfg["hooks"]["beforeShellExecution"][0]["command"]
    payload = {"command": f"cat {DOTENV}", "cwd": str(ROOT)}
    proc = _run_configured_command(command, payload, cwd=ROOT)
    out = json.loads(proc.stdout)
    assert out["permission"] == "deny"
