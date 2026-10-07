"""Regression tests for scripts/env_guard/common.py, the shared detection
logic behind the Claude Code and Cursor .env-protection hooks.

No real secrets are used or read anywhere in this file; all fixtures are
synthetic and created/destroyed by pytest's tmp_path.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts" / "env_guard"))

from common import (  # noqa: E402
    command_touches_protected,
    directory_search_exposes_protected,
    is_protected_name,
    is_protected_path,
)

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


def test_recursive_grep_over_directory_with_env_file_is_blocked(tmp_path):
    (tmp_path / PRODUCTION).write_text("SECRET=dummy\n")
    blocked, _ = command_touches_protected("grep -r SECRET .", cwd=str(tmp_path))
    assert blocked is True


def test_ripgrep_with_no_ignore_over_directory_with_env_file_is_blocked(tmp_path):
    (tmp_path / PRODUCTION).write_text("SECRET=dummy\n")
    blocked, _ = command_touches_protected(
        "rg --hidden --no-ignore SECRET .", cwd=str(tmp_path)
    )
    assert blocked is True


def test_recursive_grep_over_clean_directory_is_not_blocked(tmp_path):
    (tmp_path / "app.py").write_text("print('hi')\n")
    blocked, _ = command_touches_protected("grep -r TODO .", cwd=str(tmp_path))
    assert blocked is False


def test_directory_search_exposes_protected_detects_nested_file(tmp_path):
    nested = tmp_path / "config"
    nested.mkdir()
    (nested / DOTENV).write_text("SECRET=dummy\n")
    hit = directory_search_exposes_protected(".", str(tmp_path))
    assert hit.endswith(DOTENV)


def test_directory_search_exposes_protected_ignores_allowed_exception(tmp_path):
    (tmp_path / EXAMPLE).write_text("SECRET=\n")
    hit = directory_search_exposes_protected(".", str(tmp_path))
    assert hit == ""
