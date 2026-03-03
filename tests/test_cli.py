"""Integration tests for the OpenStation CLI (bin/openstation)."""

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

CLI = str(Path(__file__).resolve().parent.parent / "bin" / "openstation")


def run_cli(args, cwd=None):
    """Run the CLI and return (stdout, stderr, returncode)."""
    result = subprocess.run(
        [sys.executable, CLI] + args,
        capture_output=True,
        text=True,
        cwd=cwd,
    )
    return result.stdout, result.stderr, result.returncode


def make_task(base, name, status="ready", agent="researcher", owner="manual", bucket="current"):
    """Create a minimal task fixture in the vault."""
    task_dir = base / "artifacts" / "tasks" / name
    task_dir.mkdir(parents=True, exist_ok=True)
    (task_dir / "index.md").write_text(
        f"---\nkind: task\nname: {name}\nstatus: {status}\n"
        f"agent: {agent}\nowner: {owner}\ncreated: 2026-01-01\n---\n\n# {name}\n"
    )
    if bucket:
        link = base / "tasks" / bucket / name
        link.parent.mkdir(parents=True, exist_ok=True)
        link.symlink_to(task_dir.relative_to(link.parent.parent.parent))


def make_source_vault(tmpdir):
    """Create a source-repo-style vault (agents/ + install.sh)."""
    root = Path(tmpdir)
    (root / "agents").mkdir(parents=True, exist_ok=True)
    (root / "install.sh").write_text("#!/bin/bash\n")
    (root / "artifacts" / "tasks").mkdir(parents=True, exist_ok=True)
    for bucket in ("backlog", "current", "done"):
        (root / "tasks" / bucket).mkdir(parents=True, exist_ok=True)
    return root


def make_agent_spec(base, name, tools=None):
    """Create a minimal agent spec with allowed-tools."""
    if tools is None:
        tools = ["Read", "Glob", "Grep"]
    agents_dir = base / "agents"
    agents_dir.mkdir(parents=True, exist_ok=True)
    tool_lines = "\n".join(f"  - {t}" for t in tools)
    (agents_dir / f"{name}.md").write_text(
        f"---\nkind: agent\nname: {name}\n"
        f"description: Test agent\nmodel: claude-sonnet-4-6\n"
        f"allowed-tools:\n{tool_lines}\n---\n\n# {name}\n"
    )


def make_installed_vault(tmpdir):
    """Create an installed-project-style vault (.openstation/)."""
    root = Path(tmpdir)
    os_dir = root / ".openstation"
    (os_dir / "artifacts" / "tasks").mkdir(parents=True, exist_ok=True)
    for bucket in ("backlog", "current", "done"):
        (os_dir / "tasks" / bucket).mkdir(parents=True, exist_ok=True)
    return root, os_dir


# ── List Command Tests ──────────────────────────────────────────────


class TestListCommand(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.root = make_source_vault(self.tmpdir)

    def test_list_default_excludes_done_and_failed(self):
        make_task(self.root, "0001-alpha", status="ready", bucket="current")
        make_task(self.root, "0002-beta", status="done", bucket="done")
        make_task(self.root, "0003-gamma", status="failed", bucket="done")
        make_task(self.root, "0004-delta", status="in-progress", bucket="current")

        out, _, rc = run_cli(["list"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertIn("0001", out)
        self.assertIn("0004", out)
        self.assertNotIn("0002", out)
        self.assertNotIn("0003", out)

    def test_list_status_ready(self):
        make_task(self.root, "0001-alpha", status="ready", bucket="current")
        make_task(self.root, "0002-beta", status="in-progress", bucket="current")

        out, _, rc = run_cli(["list", "--status", "ready"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertIn("0001", out)
        self.assertNotIn("0002", out)

    def test_list_status_all(self):
        make_task(self.root, "0001-alpha", status="ready", bucket="current")
        make_task(self.root, "0002-beta", status="done", bucket="done")
        make_task(self.root, "0003-gamma", status="failed", bucket="done")

        out, _, rc = run_cli(["list", "--status", "all"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertIn("0001", out)
        self.assertIn("0002", out)
        self.assertIn("0003", out)

    def test_list_agent_filter(self):
        make_task(self.root, "0001-alpha", agent="researcher", bucket="current")
        make_task(self.root, "0002-beta", agent="author", bucket="current")

        out, _, rc = run_cli(["list", "--agent", "researcher"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertIn("0001", out)
        self.assertNotIn("0002", out)

    def test_list_combined_filters(self):
        make_task(self.root, "0001-alpha", status="ready", agent="researcher", bucket="current")
        make_task(self.root, "0002-beta", status="in-progress", agent="researcher", bucket="current")
        make_task(self.root, "0003-gamma", status="ready", agent="author", bucket="current")

        out, _, rc = run_cli(["list", "--status", "ready", "--agent", "researcher"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertIn("0001", out)
        self.assertNotIn("0002", out)
        self.assertNotIn("0003", out)

    def test_list_empty_results(self):
        out, _, rc = run_cli(["list"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertEqual(out.strip(), "")

    def test_list_skips_missing_index(self):
        task_dir = self.root / "artifacts" / "tasks" / "0001-noindex"
        task_dir.mkdir(parents=True)
        link = self.root / "tasks" / "current" / "0001-noindex"
        link.symlink_to(task_dir.relative_to(link.parent.parent.parent))

        out, _, rc = run_cli(["list"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertNotIn("0001", out)

    def test_list_sorted_by_id(self):
        make_task(self.root, "0003-gamma", bucket="current")
        make_task(self.root, "0001-alpha", bucket="current")
        make_task(self.root, "0002-beta", bucket="current")

        out, _, rc = run_cli(["list"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        lines = [l for l in out.strip().splitlines() if l.strip() and not l.startswith("-")]
        # Data lines (skip header + separator)
        data = lines[1:]
        ids = [l.split()[0] for l in data]
        self.assertEqual(ids, ["0001", "0002", "0003"])


# ── Show Command Tests ──────────────────────────────────────────────


class TestShowCommand(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.root = make_source_vault(self.tmpdir)

    def test_show_by_slug(self):
        make_task(self.root, "0001-alpha", bucket="current")

        out, _, rc = run_cli(["show", "0001-alpha"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertIn("kind: task", out)
        self.assertIn("0001-alpha", out)

    def test_show_by_id_prefix(self):
        make_task(self.root, "0001-alpha", bucket="current")

        out, _, rc = run_cli(["show", "0001"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertIn("kind: task", out)

    def test_show_ambiguous_prefix(self):
        make_task(self.root, "0001-alpha", bucket="current")
        make_task(self.root, "0001-beta", bucket="current")

        _, err, rc = run_cli(["show", "0001"], cwd=self.tmpdir)
        self.assertEqual(rc, 4)
        self.assertIn("ambiguous", err)
        self.assertIn("0001-alpha", err)
        self.assertIn("0001-beta", err)

    def test_show_not_found(self):
        _, err, rc = run_cli(["show", "9999"], cwd=self.tmpdir)
        self.assertEqual(rc, 3)
        self.assertIn("not found", err)

    def test_show_missing_index(self):
        task_dir = self.root / "artifacts" / "tasks" / "0001-noindex"
        task_dir.mkdir(parents=True)

        _, err, rc = run_cli(["show", "0001-noindex"], cwd=self.tmpdir)
        self.assertEqual(rc, 3)
        self.assertIn("task spec missing", err)


# ── Root Detection Tests ────────────────────────────────────────────


class TestRootDetection(unittest.TestCase):

    def test_source_repo_root(self):
        tmpdir = tempfile.mkdtemp()
        root = make_source_vault(tmpdir)
        make_task(root, "0001-alpha", bucket="current")

        out, _, rc = run_cli(["list"], cwd=tmpdir)
        self.assertEqual(rc, 0)
        self.assertIn("0001", out)

    def test_installed_project_root(self):
        tmpdir = tempfile.mkdtemp()
        root, os_dir = make_installed_vault(tmpdir)
        make_task(os_dir, "0001-alpha", bucket="current")

        out, _, rc = run_cli(["list"], cwd=tmpdir)
        self.assertEqual(rc, 0)
        self.assertIn("0001", out)

    def test_source_repo_takes_precedence(self):
        """If both .openstation/ and agents/+install.sh exist, prefer source repo."""
        tmpdir = tempfile.mkdtemp()
        root = Path(tmpdir)

        # Source repo markers
        (root / "agents").mkdir()
        (root / "install.sh").write_text("#!/bin/bash\n")
        (root / "artifacts" / "tasks").mkdir(parents=True)
        for b in ("backlog", "current", "done"):
            (root / "tasks" / b).mkdir(parents=True)

        # Installed markers with different task
        os_dir = root / ".openstation"
        (os_dir / "artifacts" / "tasks").mkdir(parents=True)
        for b in ("backlog", "current", "done"):
            (os_dir / "tasks" / b).mkdir(parents=True)

        make_task(root, "0001-source-task", bucket="current")
        make_task(os_dir, "0002-installed-task", bucket="current")

        out, _, rc = run_cli(["list", "--status", "all"], cwd=tmpdir)
        self.assertEqual(rc, 0)
        # Source repo takes precedence over .openstation/
        self.assertIn("0001", out)
        self.assertNotIn("0002", out)

    def test_child_directory_finds_root(self):
        tmpdir = tempfile.mkdtemp()
        root = make_source_vault(tmpdir)
        make_task(root, "0001-alpha", bucket="current")

        # Run from a child directory
        child = root / "some" / "nested" / "dir"
        child.mkdir(parents=True)

        out, _, rc = run_cli(["list"], cwd=str(child))
        self.assertEqual(rc, 0)
        self.assertIn("0001", out)

    def test_not_in_project(self):
        tmpdir = tempfile.mkdtemp()
        # Empty dir — no vault markers

        _, err, rc = run_cli(["list"], cwd=tmpdir)
        self.assertEqual(rc, 2)
        self.assertIn("not in an Open Station project", err)


# ── Run Command Tests ──────────────────────────────────────────────


class TestRunDryRun(unittest.TestCase):
    """Test run subcommand with --dry-run (no subprocess needed)."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.root = make_source_vault(self.tmpdir)
        make_agent_spec(self.root, "researcher")

    def test_by_agent_tier2_dry_run(self):
        out, _, rc = run_cli(["run", "researcher", "--dry-run"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertIn("claude", out)
        self.assertIn("--agent researcher", out)
        self.assertIn("--allowedTools", out)
        self.assertIn("Read", out)
        self.assertIn("--max-budget-usd 5", out)
        self.assertIn("--max-turns 50", out)
        self.assertIn("--output-format json", out)

    def test_by_agent_tier1_dry_run(self):
        out, _, rc = run_cli(["run", "researcher", "--tier", "1", "--dry-run"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertIn("claude", out)
        self.assertIn("--agent researcher", out)
        self.assertIn("--permission-mode acceptEdits", out)
        # Tier 1 should NOT include budget/turns/allowedTools
        self.assertNotIn("--allowedTools", out)
        self.assertNotIn("--max-budget-usd", out)

    def test_by_agent_custom_budget_turns(self):
        out, _, rc = run_cli(
            ["run", "researcher", "--budget", "10", "--turns", "100", "--dry-run"],
            cwd=self.tmpdir,
        )
        self.assertEqual(rc, 0)
        self.assertIn("--max-budget-usd 10", out)
        self.assertIn("--max-turns 100", out)

    def test_by_task_dry_run(self):
        make_task(self.root, "0001-alpha", status="ready", agent="researcher", bucket="current")
        out, _, rc = run_cli(["run", "--task", "0001", "--dry-run"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertIn("claude", out)
        self.assertIn("--agent researcher", out)
        self.assertIn("0001-alpha", out)  # prompt references task name

    def test_by_task_full_slug(self):
        make_task(self.root, "0001-alpha", status="ready", agent="researcher", bucket="current")
        out, _, rc = run_cli(["run", "--task", "0001-alpha", "--dry-run"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertIn("0001-alpha", out)

    def test_by_agent_with_quoted_tools(self):
        make_agent_spec(self.root, "developer", tools=["Read", "Glob", '"Bash(ls *)"'])
        out, _, rc = run_cli(["run", "developer", "--dry-run"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertIn("Bash(ls *)", out)


class TestRunArgValidation(unittest.TestCase):
    """Test argument validation for run subcommand."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.root = make_source_vault(self.tmpdir)

    def test_both_agent_and_task_errors(self):
        make_agent_spec(self.root, "researcher")
        make_task(self.root, "0001-alpha", status="ready", bucket="current")
        _, stderr, rc = run_cli(
            ["run", "researcher", "--task", "0001", "--dry-run"],
            cwd=self.tmpdir,
        )
        self.assertEqual(rc, 1)
        self.assertIn("Specify either an agent name or --task, not both", stderr)

    def test_neither_agent_nor_task_errors(self):
        _, stderr, rc = run_cli(["run", "--dry-run"], cwd=self.tmpdir)
        self.assertEqual(rc, 1)
        self.assertIn("Agent name or --task is required", stderr)

    def test_invalid_tier(self):
        _, stderr, rc = run_cli(
            ["run", "researcher", "--tier", "3", "--dry-run"],
            cwd=self.tmpdir,
        )
        self.assertNotEqual(rc, 0)

    def test_missing_agent_spec(self):
        _, stderr, rc = run_cli(
            ["run", "nonexistent", "--dry-run"],
            cwd=self.tmpdir,
        )
        self.assertEqual(rc, 2)
        self.assertIn("Agent spec not found", stderr)

    def test_missing_allowed_tools(self):
        # Create agent spec without allowed-tools
        agents_dir = self.root / "agents"
        agents_dir.mkdir(parents=True, exist_ok=True)
        (agents_dir / "empty-agent.md").write_text(
            "---\nkind: agent\nname: empty-agent\n---\n"
        )
        _, stderr, rc = run_cli(
            ["run", "empty-agent", "--dry-run"],
            cwd=self.tmpdir,
        )
        self.assertEqual(rc, 1)
        self.assertIn("No allowed-tools found", stderr)


class TestRunTaskValidation(unittest.TestCase):
    """Test task-related validation for run subcommand."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.root = make_source_vault(self.tmpdir)
        make_agent_spec(self.root, "researcher")

    def test_task_not_found(self):
        _, stderr, rc = run_cli(
            ["run", "--task", "9999", "--dry-run"],
            cwd=self.tmpdir,
        )
        self.assertEqual(rc, 3)
        self.assertIn("not found", stderr)

    def test_task_not_ready(self):
        make_task(self.root, "0001-alpha", status="in-progress", agent="researcher", bucket="current")
        _, stderr, rc = run_cli(
            ["run", "--task", "0001", "--dry-run"],
            cwd=self.tmpdir,
        )
        self.assertEqual(rc, 5)
        self.assertIn("has status 'in-progress'", stderr)
        self.assertIn("expected 'ready'", stderr)

    def test_task_not_ready_with_force(self):
        make_task(self.root, "0001-alpha", status="in-progress", agent="researcher", bucket="current")
        out, _, rc = run_cli(
            ["run", "--task", "0001", "--force", "--dry-run"],
            cwd=self.tmpdir,
        )
        self.assertEqual(rc, 0)
        self.assertIn("claude", out)

    def test_task_no_agent_assigned(self):
        make_task(self.root, "0001-alpha", status="ready", agent="", bucket="current")
        _, stderr, rc = run_cli(
            ["run", "--task", "0001", "--dry-run"],
            cwd=self.tmpdir,
        )
        self.assertEqual(rc, 1)
        self.assertIn("No agent assigned", stderr)


class TestRunSubtasks(unittest.TestCase):
    """Test subtask discovery and execution in by-task mode."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.root = make_source_vault(self.tmpdir)
        make_agent_spec(self.root, "researcher")
        make_agent_spec(self.root, "author")

    def test_no_subtasks_runs_parent(self):
        make_task(self.root, "0001-parent", status="ready", agent="researcher", bucket="current")
        out, stderr, rc = run_cli(
            ["run", "--task", "0001-parent", "--dry-run"],
            cwd=self.tmpdir,
        )
        self.assertEqual(rc, 0)
        self.assertIn("No subtasks found", stderr)
        self.assertIn("0001-parent", out)

    def test_subtask_discovery(self):
        # Create parent task
        make_task(self.root, "0001-parent", status="ready", agent="researcher", bucket="current")
        # Create subtask
        make_task(self.root, "0002-child", status="ready", agent="researcher", bucket=None)
        # Symlink subtask into parent
        parent_dir = self.root / "artifacts" / "tasks" / "0001-parent"
        child_dir = self.root / "artifacts" / "tasks" / "0002-child"
        (parent_dir / "0002-child").symlink_to(child_dir)

        out, stderr, rc = run_cli(
            ["run", "--task", "0001-parent", "--dry-run"],
            cwd=self.tmpdir,
        )
        self.assertEqual(rc, 0)
        self.assertIn("1 ready subtask", stderr)
        self.assertIn("0002-child", out)

    def test_max_tasks_limits_execution(self):
        # Create parent with two subtasks
        make_task(self.root, "0001-parent", status="ready", agent="researcher", bucket="current")
        make_task(self.root, "0002-child-a", status="ready", agent="researcher", bucket=None)
        make_task(self.root, "0003-child-b", status="ready", agent="researcher", bucket=None)

        parent_dir = self.root / "artifacts" / "tasks" / "0001-parent"
        (parent_dir / "0002-child-a").symlink_to(
            self.root / "artifacts" / "tasks" / "0002-child-a"
        )
        (parent_dir / "0003-child-b").symlink_to(
            self.root / "artifacts" / "tasks" / "0003-child-b"
        )

        out, stderr, rc = run_cli(
            ["run", "--task", "0001-parent", "--max-tasks", "1", "--dry-run"],
            cwd=self.tmpdir,
        )
        self.assertEqual(rc, 0)
        self.assertIn("2 ready subtask", stderr)
        # Only first subtask should appear in dry-run output
        self.assertIn("0002-child-a", out)
        self.assertNotIn("0003-child-b", out)

    def test_subtask_only_ready_collected(self):
        make_task(self.root, "0001-parent", status="ready", agent="researcher", bucket="current")
        make_task(self.root, "0002-ready", status="ready", agent="researcher", bucket=None)
        make_task(self.root, "0003-done", status="done", agent="researcher", bucket=None)

        parent_dir = self.root / "artifacts" / "tasks" / "0001-parent"
        (parent_dir / "0002-ready").symlink_to(
            self.root / "artifacts" / "tasks" / "0002-ready"
        )
        (parent_dir / "0003-done").symlink_to(
            self.root / "artifacts" / "tasks" / "0003-done"
        )

        out, stderr, rc = run_cli(
            ["run", "--task", "0001-parent", "--dry-run"],
            cwd=self.tmpdir,
        )
        self.assertEqual(rc, 0)
        self.assertIn("1 ready subtask", stderr)
        self.assertIn("0002-ready", out)
        self.assertNotIn("0003-done", out)


class TestRunClaude(unittest.TestCase):
    """Test run command with a mock claude binary."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.root = make_source_vault(self.tmpdir)
        make_agent_spec(self.root, "researcher")

        # Create a mock claude script that logs its args
        self.mock_bin = Path(self.tmpdir) / "_mock_bin"
        self.mock_bin.mkdir()
        self.mock_log = Path(self.tmpdir) / "claude_args.log"
        mock_claude = self.mock_bin / "claude"
        mock_claude.write_text(
            f'#!/bin/bash\necho "$@" > {self.mock_log}\nexit 0\n'
        )
        mock_claude.chmod(0o755)

        # Prepend mock to PATH for child processes
        self.env = os.environ.copy()
        self.env["PATH"] = f"{self.mock_bin}:{self.env.get('PATH', '')}"

    def _run_with_mock(self, args):
        result = subprocess.run(
            [sys.executable, CLI] + args,
            capture_output=True,
            text=True,
            cwd=self.tmpdir,
            env=self.env,
        )
        return result.stdout, result.stderr, result.returncode

    def test_by_task_executes_mock_claude(self):
        make_task(self.root, "0001-alpha", status="ready", agent="researcher", bucket="current")
        _, stderr, rc = self._run_with_mock(["run", "--task", "0001"])
        self.assertEqual(rc, 0, f"stderr: {stderr}")
        # Verify mock claude was called
        self.assertTrue(self.mock_log.exists(), "Mock claude was not invoked")
        args = self.mock_log.read_text()
        self.assertIn("--agent researcher", args)
        self.assertIn("0001-alpha", args)

    def test_claude_not_on_path(self):
        # Use an empty PATH so claude is not found
        env = os.environ.copy()
        env["PATH"] = ""
        result = subprocess.run(
            [sys.executable, CLI, "run", "researcher"],
            capture_output=True,
            text=True,
            cwd=self.tmpdir,
            env=env,
        )
        self.assertEqual(result.returncode, 3)
        self.assertIn("claude CLI not found", result.stderr)


if __name__ == "__main__":
    unittest.main()
