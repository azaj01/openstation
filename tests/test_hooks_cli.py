"""Tests for hooks CLI subcommands: list, show, run."""

import json

import pytest

from openstation import hooks, core


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def vault(tmp_path):
    """Create a minimal vault with .openstation/ layout and a task."""
    os_dir = tmp_path / ".openstation"
    os_dir.mkdir()
    tasks_dir = os_dir / "artifacts" / "tasks"
    tasks_dir.mkdir(parents=True)
    task_file = tasks_dir / "0001-test-task.md"
    task_file.write_text(
        "---\nkind: task\nname: 0001-test-task\nstatus: in-progress\n---\n"
    )
    return tmp_path


def write_settings(vault, hook_entries):
    """Write a settings.json with the given StatusTransition hooks."""
    settings = {"hooks": {"StatusTransition": hook_entries}}
    (vault / ".openstation" / "settings.json").write_text(json.dumps(settings))


class FakeArgs:
    """Minimal args namespace for testing."""
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


# ---------------------------------------------------------------------------
# hooks list
# ---------------------------------------------------------------------------

class TestHooksList:
    def test_no_hooks(self, vault, capsys):
        rc = hooks.cmd_hooks_list(FakeArgs(), vault)
        assert rc == core.EXIT_OK
        assert "No hooks configured" in capsys.readouterr().out

    def test_lists_hooks_table(self, vault, capsys):
        write_settings(vault, [
            {"matcher": "*→done", "command": "echo done"},
            {"matcher": "in-progress→review", "command": "bin/lint", "phase": "post", "timeout": 60},
        ])
        rc = hooks.cmd_hooks_list(FakeArgs(), vault)
        assert rc == core.EXIT_OK
        out = capsys.readouterr().out
        assert "*→done" in out
        assert "echo done" in out
        assert "pre" in out
        assert "in-progress→review" in out
        assert "bin/lint" in out
        assert "post" in out
        assert "60s" in out

    def test_default_timeout_shown(self, vault, capsys):
        write_settings(vault, [{"matcher": "*→*", "command": "true"}])
        hooks.cmd_hooks_list(FakeArgs(), vault)
        out = capsys.readouterr().out
        assert "30s" in out


# ---------------------------------------------------------------------------
# hooks show
# ---------------------------------------------------------------------------

class TestHooksShow:
    def test_show_by_index(self, vault, capsys):
        write_settings(vault, [
            {"matcher": "*→done", "command": "echo done", "timeout": 45},
        ])
        rc = hooks.cmd_hooks_show(FakeArgs(hook_query="0"), vault)
        assert rc == core.EXIT_OK
        out = capsys.readouterr().out
        assert "Index:   0" in out
        assert "*→done" in out
        assert "echo done" in out
        assert "45s" in out

    def test_show_by_matcher(self, vault, capsys):
        write_settings(vault, [
            {"matcher": "*→done", "command": "echo done"},
            {"matcher": "ready→in-progress", "command": "echo start"},
        ])
        rc = hooks.cmd_hooks_show(FakeArgs(hook_query="ready→in-progress"), vault)
        assert rc == core.EXIT_OK
        out = capsys.readouterr().out
        assert "Index:   1" in out
        assert "echo start" in out

    def test_show_by_ascii_matcher(self, vault, capsys):
        write_settings(vault, [
            {"matcher": "*->done", "command": "echo done"},
        ])
        rc = hooks.cmd_hooks_show(FakeArgs(hook_query="*->done"), vault)
        assert rc == core.EXIT_OK
        out = capsys.readouterr().out
        assert "echo done" in out

    def test_show_index_out_of_range(self, vault, capsys):
        write_settings(vault, [{"matcher": "*→*", "command": "true"}])
        rc = hooks.cmd_hooks_show(FakeArgs(hook_query="5"), vault)
        assert rc == core.EXIT_NOT_FOUND

    def test_show_no_hooks(self, vault):
        rc = hooks.cmd_hooks_show(FakeArgs(hook_query="0"), vault)
        assert rc == core.EXIT_NOT_FOUND

    def test_show_matcher_not_found(self, vault):
        write_settings(vault, [{"matcher": "*→done", "command": "true"}])
        rc = hooks.cmd_hooks_show(FakeArgs(hook_query="backlog→ready"), vault)
        assert rc == core.EXIT_NOT_FOUND

    def test_show_ambiguous_matcher(self, vault):
        write_settings(vault, [
            {"matcher": "*→done", "command": "echo first"},
            {"matcher": "*→done", "command": "echo second"},
        ])
        rc = hooks.cmd_hooks_show(FakeArgs(hook_query="*→done"), vault)
        assert rc == core.EXIT_AMBIGUOUS


# ---------------------------------------------------------------------------
# hooks run
# ---------------------------------------------------------------------------

class TestHooksRun:
    def test_dry_run(self, vault, capsys):
        write_settings(vault, [
            {"matcher": "*→review", "command": "echo check"},
            {"matcher": "*→*", "command": "echo all", "phase": "post"},
        ])
        rc = hooks.cmd_hooks_run(
            FakeArgs(task="0001", old_status="in-progress", new_status="review",
                     phase="all", dry_run=True),
            vault,
        )
        assert rc == core.EXIT_OK
        out = capsys.readouterr().out
        assert "Dry run" in out
        assert "echo check" in out
        assert "echo all" in out

    def test_dry_run_phase_filter(self, vault, capsys):
        write_settings(vault, [
            {"matcher": "*→review", "command": "echo pre-hook"},
            {"matcher": "*→review", "command": "echo post-hook", "phase": "post"},
        ])
        rc = hooks.cmd_hooks_run(
            FakeArgs(task="0001", old_status="in-progress", new_status="review",
                     phase="pre", dry_run=True),
            vault,
        )
        assert rc == core.EXIT_OK
        out = capsys.readouterr().out
        assert "echo pre-hook" in out
        assert "echo post-hook" not in out

    def test_dry_run_post_only(self, vault, capsys):
        write_settings(vault, [
            {"matcher": "*→review", "command": "echo pre-hook"},
            {"matcher": "*→review", "command": "echo post-hook", "phase": "post"},
        ])
        rc = hooks.cmd_hooks_run(
            FakeArgs(task="0001", old_status="in-progress", new_status="review",
                     phase="post", dry_run=True),
            vault,
        )
        assert rc == core.EXIT_OK
        out = capsys.readouterr().out
        assert "echo pre-hook" not in out
        assert "echo post-hook" in out

    def test_no_matching_hooks(self, vault, capsys):
        write_settings(vault, [
            {"matcher": "backlog→ready", "command": "echo nope"},
        ])
        rc = hooks.cmd_hooks_run(
            FakeArgs(task="0001", old_status="in-progress", new_status="review",
                     phase="all", dry_run=False),
            vault,
        )
        assert rc == core.EXIT_OK
        assert "No hooks match" in capsys.readouterr().out

    def test_run_executes_hooks(self, vault, capsys):
        marker = vault / "hook_ran.txt"
        write_settings(vault, [
            {"matcher": "*→review", "command": f"touch {marker}"},
        ])
        rc = hooks.cmd_hooks_run(
            FakeArgs(task="0001", old_status="in-progress", new_status="review",
                     phase="all", dry_run=False),
            vault,
        )
        assert rc == core.EXIT_OK
        assert marker.exists()

    def test_run_sets_env_vars(self, vault, capsys):
        out_file = vault / "env_out.txt"
        cmd = f'echo "$OS_TASK_NAME $OS_OLD_STATUS $OS_NEW_STATUS" > {out_file}'
        write_settings(vault, [{"matcher": "*→*", "command": cmd}])
        rc = hooks.cmd_hooks_run(
            FakeArgs(task="0001", old_status="in-progress", new_status="review",
                     phase="all", dry_run=False),
            vault,
        )
        assert rc == core.EXIT_OK
        content = out_file.read_text().strip()
        assert content == "0001-test-task in-progress review"

    def test_run_pre_hook_failure_returns_exit_code(self, vault):
        write_settings(vault, [{"matcher": "*→*", "command": "false"}])
        rc = hooks.cmd_hooks_run(
            FakeArgs(task="0001", old_status="in-progress", new_status="review",
                     phase="all", dry_run=False),
            vault,
        )
        assert rc == core.EXIT_HOOK_FAILED

    def test_run_post_hook_failure_returns_ok(self, vault):
        write_settings(vault, [
            {"matcher": "*→*", "command": "false", "phase": "post"},
        ])
        rc = hooks.cmd_hooks_run(
            FakeArgs(task="0001", old_status="in-progress", new_status="review",
                     phase="all", dry_run=False),
            vault,
        )
        assert rc == core.EXIT_OK

    def test_invalid_old_status(self, vault):
        rc = hooks.cmd_hooks_run(
            FakeArgs(task="0001", old_status="bogus", new_status="review",
                     phase="all", dry_run=False),
            vault,
        )
        assert rc == core.EXIT_USAGE

    def test_invalid_new_status(self, vault):
        rc = hooks.cmd_hooks_run(
            FakeArgs(task="0001", old_status="ready", new_status="bogus",
                     phase="all", dry_run=False),
            vault,
        )
        assert rc == core.EXIT_USAGE

    def test_task_not_found(self, vault):
        write_settings(vault, [{"matcher": "*→*", "command": "true"}])
        rc = hooks.cmd_hooks_run(
            FakeArgs(task="9999", old_status="ready", new_status="in-progress",
                     phase="all", dry_run=False),
            vault,
        )
        assert rc == core.EXIT_NOT_FOUND
