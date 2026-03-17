"""Tests for CLI defaults from settings.json."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

SRC_DIR = str(Path(__file__).resolve().parent.parent / "src")


def run_cli(args, cwd=None, env=None):
    """Run the CLI and return (stdout, stderr, returncode).

    When *env* is ``None``, CLAUDECODE is stripped from the inherited
    environment so that defaults apply.  When *env* is passed
    explicitly, it is used as-is (caller controls CLAUDECODE).
    """
    if env is not None:
        run_env = dict(env)
    else:
        run_env = dict(os.environ)
        run_env.pop("CLAUDECODE", None)
    existing = run_env.get("PYTHONPATH", "")
    run_env["PYTHONPATH"] = SRC_DIR + (os.pathsep + existing if existing else "")
    result = subprocess.run(
        [sys.executable, "-m", "openstation"] + args,
        capture_output=True,
        text=True,
        cwd=cwd,
        env=run_env,
        timeout=30,
    )
    return result.stdout, result.stderr, result.returncode


def make_source_vault(tmpdir):
    """Create a source-repo-style vault."""
    root = Path(tmpdir)
    (root / "agents").mkdir(parents=True, exist_ok=True)
    (root / "install.sh").write_text("#!/bin/bash\n")
    (root / "artifacts" / "tasks").mkdir(parents=True, exist_ok=True)
    return root


def make_task(root, name, status="ready"):
    tasks_dir = root / "artifacts" / "tasks"
    tasks_dir.mkdir(parents=True, exist_ok=True)
    (tasks_dir / f"{name}.md").write_text(
        f"---\nkind: task\nname: {name}\nstatus: {status}\n"
        f"assignee: dev\nowner: user\ncreated: 2026-01-01\n---\n\n# {name}\n"
    )


def write_settings(root, settings):
    (root / "settings.json").write_text(json.dumps(settings))


# ---------------------------------------------------------------------------
# Unit tests for _apply_cli_defaults and _command_key
# ---------------------------------------------------------------------------

from openstation.cli import _apply_cli_defaults, _command_key, _explicit_flags
from argparse import Namespace


class TestExplicitFlags:
    def test_long_flag(self):
        assert "json" in _explicit_flags(["show", "0042", "--json"])

    def test_long_flag_with_dashes(self):
        assert "dry_run" in _explicit_flags(["run", "--dry-run"])

    def test_short_flag_j(self):
        assert "json" in _explicit_flags(["show", "0042", "-j"])

    def test_short_flag_v(self):
        assert "vim" in _explicit_flags(["show", "0042", "-v"])

    def test_no_flags(self):
        assert _explicit_flags(["show", "0042"]) == set()

    def test_stops_at_double_dash(self):
        flags = _explicit_flags(["show", "--", "--json"])
        assert "json" not in flags

    def test_flag_with_equals(self):
        assert "status" in _explicit_flags(["list", "--status=ready"])

    def test_does_not_apply_when_explicit(self):
        """Explicit --json prevents vim default from being applied."""
        args = Namespace(command="show", vim=False, json=True)
        settings = {"defaults": {"show": {"vim": True}}}
        _apply_cli_defaults(args, settings, argv=["show", "0042", "--json"])
        assert args.vim is False


class TestCommandKey:
    def test_simple_command(self):
        args = Namespace(command="show")
        assert _command_key(args) == "show"

    def test_list_command(self):
        args = Namespace(command="list")
        assert _command_key(args) == "list"

    def test_agents_show(self):
        args = Namespace(command="agents", agents_action="show")
        assert _command_key(args) == "agents.show"

    def test_agents_alias(self):
        args = Namespace(command="ag", agents_action="show")
        assert _command_key(args) == "agents.show"

    def test_artifacts_list(self):
        args = Namespace(command="artifacts", artifacts_action="list")
        assert _command_key(args) == "artifacts.list"

    def test_artifacts_alias(self):
        args = Namespace(command="art", artifacts_action="list")
        assert _command_key(args) == "artifacts.list"

    def test_no_subaction(self):
        args = Namespace(command="agents")
        assert _command_key(args) == "agents"


class TestApplyCliDefaults:
    def test_sets_boolean_flag(self):
        args = Namespace(command="show", vim=False, json=False)
        settings = {"defaults": {"show": {"vim": True}}}
        _apply_cli_defaults(args, settings, argv=[])
        assert args.vim is True

    def test_does_not_override_explicit_flag(self):
        args = Namespace(command="show", vim=True, json=False)
        settings = {"defaults": {"show": {"vim": False}}}
        _apply_cli_defaults(args, settings, argv=["show", "0042", "--vim"])
        assert args.vim is True  # explicit wins

    def test_sets_string_flag_from_none(self):
        args = Namespace(command="list", status=None)
        settings = {"defaults": {"list": {"status": "ready"}}}
        _apply_cli_defaults(args, settings, argv=[])
        assert args.status == "ready"

    def test_sets_string_flag_from_empty(self):
        args = Namespace(command="list", assignee="")
        settings = {"defaults": {"list": {"assignee": "dev"}}}
        _apply_cli_defaults(args, settings, argv=[])
        assert args.assignee == "dev"

    def test_does_not_override_explicit_string(self):
        args = Namespace(command="list", status="done")
        settings = {"defaults": {"list": {"status": "ready"}}}
        _apply_cli_defaults(args, settings, argv=["list", "--status", "done"])
        assert args.status == "done"

    def test_no_defaults_key(self):
        args = Namespace(command="show", vim=False)
        _apply_cli_defaults(args, {"hooks": {}})
        assert args.vim is False

    def test_no_command_defaults(self):
        args = Namespace(command="show", vim=False)
        settings = {"defaults": {"list": {"vim": True}}}
        _apply_cli_defaults(args, settings, argv=[])
        assert args.vim is False

    def test_invalid_defaults_type(self):
        args = Namespace(command="show", vim=False)
        _apply_cli_defaults(args, {"defaults": "bad"})
        assert args.vim is False

    def test_invalid_command_defaults_type(self):
        args = Namespace(command="show", vim=False)
        _apply_cli_defaults(args, {"defaults": {"show": "bad"}})
        assert args.vim is False

    def test_empty_settings(self):
        args = Namespace(command="show", vim=False)
        _apply_cli_defaults(args, {})
        assert args.vim is False

    def test_nested_command_key(self):
        args = Namespace(command="agents", agents_action="show", vim=False, json=False)
        settings = {"defaults": {"agents.show": {"vim": True}}}
        _apply_cli_defaults(args, settings, argv=[])
        assert args.vim is True


# ---------------------------------------------------------------------------
# Integration: defaults skipped in agent context (CLAUDECODE set)
# ---------------------------------------------------------------------------

class TestAgentContextSkipsDefaults:
    def test_show_ignores_defaults_when_claudecode_set(self, tmp_path):
        """With CLAUDECODE set, defaults.show.json is ignored."""
        root = make_source_vault(tmp_path)
        make_task(root, "0001-test-task")
        # json=true in defaults — but CLAUDECODE should skip it
        write_settings(root, {"defaults": {"show": {"json": True}}})

        env = dict(os.environ)
        env["CLAUDECODE"] = "1"
        existing = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = SRC_DIR + (os.pathsep + existing if existing else "")

        stdout, stderr, rc = run_cli(
            ["show", "0001-test-task"], cwd=str(root), env=env,
        )
        # Should print raw markdown (not JSON) since defaults are skipped
        assert rc == 0
        assert "0001-test-task" in stdout
        # Confirm it's NOT json
        with pytest.raises(json.JSONDecodeError):
            json.loads(stdout)

    def test_show_applies_defaults_for_human(self, tmp_path):
        """Without CLAUDECODE, defaults.show.json applies."""
        root = make_source_vault(tmp_path)
        make_task(root, "0001-test-task")
        # Use json=true as a testable default (vim would exec into editor)
        write_settings(root, {"defaults": {"show": {"json": True}}})

        stdout, stderr, rc = run_cli(
            ["show", "0001-test-task"], cwd=str(root),
        )
        assert rc == 0
        # Should be valid JSON
        data = json.loads(stdout)
        assert data["name"] == "0001-test-task"


# ---------------------------------------------------------------------------
# Integration: explicit flags override defaults
# ---------------------------------------------------------------------------

class TestExplicitOverridesDefault:
    def test_explicit_json_overrides_default_vim(self, tmp_path):
        """--json flag takes precedence over defaults.show.vim."""
        root = make_source_vault(tmp_path)
        make_task(root, "0001-test-task")
        # defaults say vim, but user passes --json
        write_settings(root, {"defaults": {"show": {"vim": True}}})

        stdout, stderr, rc = run_cli(
            ["show", "0001-test-task", "--json"], cwd=str(root),
        )
        assert rc == 0
        data = json.loads(stdout)
        assert data["name"] == "0001-test-task"
