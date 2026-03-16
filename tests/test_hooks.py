"""Tests for openstation.hooks — lifecycle hook loading, matching, and execution."""

import json

import pytest

from openstation import hooks, core


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def vault(tmp_path):
    """Create a minimal vault with a settings.json and a task file."""
    # Source-repo layout (prefix="")
    (tmp_path / "agents").mkdir()
    (tmp_path / "install.sh").touch()
    tasks_dir = tmp_path / "artifacts" / "tasks"
    tasks_dir.mkdir(parents=True)
    task_file = tasks_dir / "0001-test-task.md"
    task_file.write_text("---\nkind: task\nname: 0001-test-task\nstatus: ready\n---\n")
    return tmp_path


def write_settings(vault, hook_entries):
    """Write a settings.json with the given StatusTransition hooks."""
    settings = {"hooks": {"StatusTransition": hook_entries}}
    (vault / "settings.json").write_text(json.dumps(settings))


# ---------------------------------------------------------------------------
# load_hooks
# ---------------------------------------------------------------------------

class TestLoadHooks:
    def test_no_settings_file(self, vault):
        result = hooks.load_hooks(vault, "")
        assert result == []

    def test_empty_settings(self, vault):
        (vault / "settings.json").write_text("{}")
        assert hooks.load_hooks(vault, "") == []

    def test_no_status_transition_key(self, vault):
        (vault / "settings.json").write_text('{"hooks": {}}')
        assert hooks.load_hooks(vault, "") == []

    def test_loads_entries(self, vault):
        entries = [{"matcher": "*→done", "command": "echo done"}]
        write_settings(vault, entries)
        result = hooks.load_hooks(vault, "")
        assert len(result) == 1
        assert result[0]["command"] == "echo done"

    def test_installed_project_prefix(self, tmp_path):
        os_dir = tmp_path / ".openstation"
        os_dir.mkdir()
        settings = {"hooks": {"StatusTransition": [{"matcher": "*→*", "command": "true"}]}}
        (os_dir / "settings.json").write_text(json.dumps(settings))
        result = hooks.load_hooks(tmp_path, ".openstation")
        assert len(result) == 1

    def test_invalid_json(self, vault):
        (vault / "settings.json").write_text("not json")
        assert hooks.load_hooks(vault, "") == []

    def test_hooks_not_dict(self, vault):
        (vault / "settings.json").write_text('{"hooks": "bad"}')
        assert hooks.load_hooks(vault, "") == []

    def test_status_transition_not_list(self, vault):
        (vault / "settings.json").write_text('{"hooks": {"StatusTransition": "bad"}}')
        assert hooks.load_hooks(vault, "") == []


# ---------------------------------------------------------------------------
# match_hooks
# ---------------------------------------------------------------------------

class TestMatchHooks:
    def test_exact_match(self):
        h = [{"matcher": "in-progress→review", "command": "echo 1"}]
        assert len(hooks.match_hooks(h, "in-progress", "review")) == 1
        assert len(hooks.match_hooks(h, "ready", "in-progress")) == 0

    def test_wildcard_left(self):
        h = [{"matcher": "*→done", "command": "echo 1"}]
        assert len(hooks.match_hooks(h, "review", "done")) == 1
        assert len(hooks.match_hooks(h, "review", "failed")) == 0

    def test_wildcard_right(self):
        h = [{"matcher": "review→*", "command": "echo 1"}]
        assert len(hooks.match_hooks(h, "review", "done")) == 1
        assert len(hooks.match_hooks(h, "review", "failed")) == 1
        assert len(hooks.match_hooks(h, "in-progress", "review")) == 0

    def test_catch_all(self):
        h = [{"matcher": "*→*", "command": "echo 1"}]
        assert len(hooks.match_hooks(h, "ready", "in-progress")) == 1

    def test_ascii_arrow(self):
        h = [{"matcher": "*->done", "command": "echo 1"}]
        assert len(hooks.match_hooks(h, "review", "done")) == 1

    def test_declaration_order(self):
        h = [
            {"matcher": "*→*", "command": "echo first"},
            {"matcher": "*→done", "command": "echo second"},
        ]
        matched = hooks.match_hooks(h, "review", "done")
        assert len(matched) == 2
        assert matched[0]["command"] == "echo first"
        assert matched[1]["command"] == "echo second"

    def test_no_arrow_skipped(self):
        h = [{"matcher": "garbage", "command": "echo 1"}]
        assert hooks.match_hooks(h, "ready", "done") == []

    def test_missing_matcher(self):
        h = [{"command": "echo 1"}]
        assert hooks.match_hooks(h, "ready", "done") == []


# ---------------------------------------------------------------------------
# run_matched (integration)
# ---------------------------------------------------------------------------

class TestRunMatched:
    def test_no_hooks_returns_none(self, vault):
        result = hooks.run_matched(
            vault, "", "0001-test-task", "ready", "in-progress",
            vault / "artifacts" / "tasks" / "0001-test-task.md",
        )
        assert result is None

    def test_successful_hook(self, vault):
        write_settings(vault, [{"matcher": "*→*", "command": "true"}])
        result = hooks.run_matched(
            vault, "", "0001-test-task", "ready", "in-progress",
            vault / "artifacts" / "tasks" / "0001-test-task.md",
        )
        assert result is None

    def test_failing_hook_returns_exit_code(self, vault):
        write_settings(vault, [{"matcher": "*→*", "command": "false"}])
        result = hooks.run_matched(
            vault, "", "0001-test-task", "ready", "in-progress",
            vault / "artifacts" / "tasks" / "0001-test-task.md",
        )
        assert result == core.EXIT_HOOK_FAILED

    def test_env_vars_passed(self, vault):
        # Write a hook that checks env vars by writing them to a file
        out = vault / "env_out.txt"
        cmd = f'echo "$OS_TASK_NAME $OS_OLD_STATUS $OS_NEW_STATUS" > {out}'
        write_settings(vault, [{"matcher": "*→*", "command": cmd}])
        hooks.run_matched(
            vault, "", "0001-test-task", "ready", "in-progress",
            vault / "artifacts" / "tasks" / "0001-test-task.md",
        )
        content = out.read_text().strip()
        assert content == "0001-test-task ready in-progress"

    def test_env_vars_file_and_root(self, vault):
        out = vault / "env_out2.txt"
        task_file = vault / "artifacts" / "tasks" / "0001-test-task.md"
        cmd = f'echo "$OS_TASK_FILE|$OS_VAULT_ROOT" > {out}'
        write_settings(vault, [{"matcher": "*→*", "command": cmd}])
        hooks.run_matched(vault, "", "0001-test-task", "ready", "in-progress", task_file)
        content = out.read_text().strip()
        parts = content.split("|")
        assert parts[0] == str(task_file.resolve())
        assert parts[1] == str(vault.resolve())

    def test_multiple_hooks_run_in_order(self, vault):
        out = vault / "order.txt"
        write_settings(vault, [
            {"matcher": "*→*", "command": f'echo first >> {out}'},
            {"matcher": "*→*", "command": f'echo second >> {out}'},
        ])
        hooks.run_matched(
            vault, "", "0001-test-task", "ready", "in-progress",
            vault / "artifacts" / "tasks" / "0001-test-task.md",
        )
        lines = out.read_text().strip().splitlines()
        assert lines == ["first", "second"]

    def test_failure_aborts_remaining(self, vault):
        out = vault / "abort.txt"
        write_settings(vault, [
            {"matcher": "*→*", "command": "false"},
            {"matcher": "*→*", "command": f'echo should-not-run >> {out}'},
        ])
        result = hooks.run_matched(
            vault, "", "0001-test-task", "ready", "in-progress",
            vault / "artifacts" / "tasks" / "0001-test-task.md",
        )
        assert result == core.EXIT_HOOK_FAILED
        assert not out.exists()

    def test_timeout_kills_hook(self, vault):
        write_settings(vault, [
            {"matcher": "*→*", "command": "sleep 60", "timeout": 1},
        ])
        result = hooks.run_matched(
            vault, "", "0001-test-task", "ready", "in-progress",
            vault / "artifacts" / "tasks" / "0001-test-task.md",
        )
        assert result == core.EXIT_HOOK_FAILED


# ---------------------------------------------------------------------------
# CLI integration (openstation status with hooks)
# ---------------------------------------------------------------------------

class TestCLIIntegration:
    def test_status_fires_hook(self, vault):
        """A passing hook allows the transition to proceed."""
        marker = vault / "hook_ran.txt"
        write_settings(vault, [
            {"matcher": "ready→in-progress", "command": f"touch {marker}"},
        ])
        # Simulate what cmd_status does: load, match, run
        task_file = vault / "artifacts" / "tasks" / "0001-test-task.md"
        result = hooks.run_matched(vault, "", "0001-test-task", "ready", "in-progress", task_file)
        assert result is None
        assert marker.exists()

    def test_status_aborts_on_hook_failure(self, vault):
        """A failing hook prevents the transition."""
        write_settings(vault, [
            {"matcher": "ready→in-progress", "command": "exit 1"},
        ])
        task_file = vault / "artifacts" / "tasks" / "0001-test-task.md"
        result = hooks.run_matched(vault, "", "0001-test-task", "ready", "in-progress", task_file)
        assert result == core.EXIT_HOOK_FAILED
        # Task file should still be at ready
        text = task_file.read_text()
        assert "status: ready" in text
