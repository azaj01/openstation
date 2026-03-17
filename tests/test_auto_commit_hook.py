"""Tests for bin/hooks/auto-commit — the auto-commit post-hook script.

These tests verify the script's guard clauses and no-op behavior.
The actual claude -p invocation is not tested (requires Claude Code).
"""

import os
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parent.parent / "bin" / "hooks" / "auto-commit"


def run_hook(env, cwd=None, timeout=10):
    """Run the auto-commit script with the given environment."""
    full_env = os.environ.copy()
    full_env.update(env)
    # Ensure claude is NOT on PATH so we test the guard
    # (strip any claude from PATH to avoid actual invocations)
    result = subprocess.run(
        [str(SCRIPT)],
        env=full_env,
        capture_output=True,
        text=True,
        timeout=timeout,
        cwd=cwd,
    )
    return result


@pytest.fixture
def git_repo(tmp_path):
    """Create a minimal git repo with a task file."""
    subprocess.run(["git", "init", str(tmp_path)], capture_output=True, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"],
        cwd=tmp_path, capture_output=True, check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test"],
        cwd=tmp_path, capture_output=True, check=True,
    )
    # Initial commit so git diff works
    readme = tmp_path / "README.md"
    readme.write_text("# test\n")
    subprocess.run(["git", "add", "."], cwd=tmp_path, capture_output=True, check=True)
    subprocess.run(
        ["git", "commit", "-m", "initial"],
        cwd=tmp_path, capture_output=True, check=True,
    )
    # Create task file
    tasks_dir = tmp_path / "artifacts" / "tasks"
    tasks_dir.mkdir(parents=True)
    task_file = tasks_dir / "0099-test-task.md"
    task_file.write_text(
        "---\nkind: task\nname: 0099-test-task\nstatus: done\n---\n# Test Task\n"
    )
    return tmp_path


def make_env(git_repo, task_name="0099-test-task"):
    """Build the OS_ environment variables for the hook."""
    task_file = git_repo / "artifacts" / "tasks" / f"{task_name}.md"
    return {
        "OS_TASK_NAME": task_name,
        "OS_TASK_FILE": str(task_file),
        "OS_VAULT_ROOT": str(git_repo),
    }


class TestEnvGuards:
    """Script exits with error when required env vars are missing."""

    def test_missing_task_name(self, git_repo):
        env = make_env(git_repo)
        del env["OS_TASK_NAME"]
        result = run_hook(env, cwd=git_repo)
        assert result.returncode != 0
        assert "OS_TASK_NAME" in result.stderr

    def test_missing_task_file(self, git_repo):
        env = make_env(git_repo)
        del env["OS_TASK_FILE"]
        result = run_hook(env, cwd=git_repo)
        assert result.returncode != 0
        assert "OS_TASK_FILE" in result.stderr

    def test_missing_vault_root(self, git_repo):
        env = make_env(git_repo)
        del env["OS_VAULT_ROOT"]
        result = run_hook(env, cwd=git_repo)
        assert result.returncode != 0
        assert "OS_VAULT_ROOT" in result.stderr


class TestNoChangesGuard:
    """Script exits 0 (no-op) when there are no uncommitted changes."""

    def test_clean_repo_exits_zero(self, git_repo):
        # Commit the task file so repo is clean
        subprocess.run(["git", "add", "."], cwd=git_repo, capture_output=True, check=True)
        subprocess.run(
            ["git", "commit", "-m", "add task"],
            cwd=git_repo, capture_output=True, check=True,
        )
        env = make_env(git_repo)
        result = run_hook(env, cwd=git_repo)
        assert result.returncode == 0
        assert "no uncommitted changes" in result.stdout


class TestClaudeMissing:
    """Script exits 0 when claude is not available."""

    def test_no_claude_on_path(self, git_repo):
        env = make_env(git_repo)
        # Set PATH to only basic system dirs (no claude)
        env["PATH"] = "/usr/bin:/bin"
        result = run_hook(env, cwd=git_repo)
        assert result.returncode == 0
        assert "claude not found" in result.stderr or "no uncommitted changes" in result.stdout
