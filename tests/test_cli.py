"""Integration tests for the OpenStation CLI (bin/openstation)."""

import os
import re
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


def make_task(base, name, status="ready", agent="researcher", owner="manual",
              subtasks=None):
    """Create a minimal task fixture in the vault."""
    tasks_dir = base / "artifacts" / "tasks"
    tasks_dir.mkdir(parents=True, exist_ok=True)
    extra = ""
    if subtasks:
        extra = "subtasks:\n" + "".join(f"  - {s}\n" for s in subtasks)
    (tasks_dir / f"{name}.md").write_text(
        f"---\nkind: task\nname: {name}\nstatus: {status}\n"
        f"agent: {agent}\nowner: {owner}\ncreated: 2026-01-01\n"
        f"{extra}---\n\n# {name}\n"
    )


def make_source_vault(tmpdir):
    """Create a source-repo-style vault (agents/ + install.sh)."""
    root = Path(tmpdir)
    (root / "agents").mkdir(parents=True, exist_ok=True)
    (root / "install.sh").write_text("#!/bin/bash\n")
    (root / "artifacts" / "tasks").mkdir(parents=True, exist_ok=True)
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
    return root, os_dir


# ── List Command Tests ──────────────────────────────────────────────


class TestListCommand(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.root = make_source_vault(self.tmpdir)

    def test_list_default_shows_only_active(self):
        make_task(self.root, "0001-alpha", status="ready")
        make_task(self.root, "0002-beta", status="done")
        make_task(self.root, "0003-gamma", status="failed")
        make_task(self.root, "0004-delta", status="in-progress")
        make_task(self.root, "0005-epsilon", status="backlog")
        make_task(self.root, "0006-zeta", status="review")

        out, _, rc = run_cli(["list"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertIn("0001", out)   # ready — included
        self.assertIn("0004", out)   # in-progress — included
        self.assertIn("0006", out)   # review — included
        self.assertNotIn("0002", out)  # done — excluded
        self.assertNotIn("0003", out)  # failed — excluded
        self.assertNotIn("0005", out)  # backlog — excluded

    def test_list_status_backlog(self):
        make_task(self.root, "0001-alpha", status="backlog")
        make_task(self.root, "0002-beta", status="ready")

        out, _, rc = run_cli(["list", "--status", "backlog"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertIn("0001", out)
        self.assertNotIn("0002", out)

    def test_list_status_ready(self):
        make_task(self.root, "0001-alpha", status="ready")
        make_task(self.root, "0002-beta", status="in-progress")

        out, _, rc = run_cli(["list", "--status", "ready"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertIn("0001", out)
        self.assertNotIn("0002", out)

    def test_list_status_all(self):
        make_task(self.root, "0001-alpha", status="ready")
        make_task(self.root, "0002-beta", status="done")
        make_task(self.root, "0003-gamma", status="failed")

        out, _, rc = run_cli(["list", "--status", "all"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertIn("0001", out)
        self.assertIn("0002", out)
        self.assertIn("0003", out)

    def test_list_agent_filter(self):
        make_task(self.root, "0001-alpha", agent="researcher")
        make_task(self.root, "0002-beta", agent="author")

        out, _, rc = run_cli(["list", "--agent", "researcher"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertIn("0001", out)
        self.assertNotIn("0002", out)

    def test_list_combined_filters(self):
        make_task(self.root, "0001-alpha", status="ready", agent="researcher")
        make_task(self.root, "0002-beta", status="in-progress", agent="researcher")
        make_task(self.root, "0003-gamma", status="ready", agent="author")

        out, _, rc = run_cli(["list", "--status", "ready", "--agent", "researcher"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertIn("0001", out)
        self.assertNotIn("0002", out)
        self.assertNotIn("0003", out)

    def test_list_empty_results(self):
        out, _, rc = run_cli(["list"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertEqual(out.strip(), "")

    def test_list_skips_non_task_files(self):
        # A .md file without kind: task should be skipped
        tasks_dir = self.root / "artifacts" / "tasks"
        tasks_dir.mkdir(parents=True, exist_ok=True)
        (tasks_dir / "roadmap.md").write_text("# Roadmap\nNot a task.\n")

        out, _, rc = run_cli(["list"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertNotIn("roadmap", out)

    def test_list_sorted_by_id(self):
        make_task(self.root, "0003-gamma")
        make_task(self.root, "0001-alpha")
        make_task(self.root, "0002-beta")

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
        make_task(self.root, "0001-alpha")

        out, _, rc = run_cli(["show", "0001-alpha"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertIn("kind: task", out)
        self.assertIn("0001-alpha", out)

    def test_show_by_id_prefix(self):
        make_task(self.root, "0001-alpha")

        out, _, rc = run_cli(["show", "0001"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertIn("kind: task", out)

    def test_show_ambiguous_prefix(self):
        make_task(self.root, "0001-alpha")
        make_task(self.root, "0001-beta")

        _, err, rc = run_cli(["show", "0001"], cwd=self.tmpdir)
        self.assertEqual(rc, 4)
        self.assertIn("ambiguous", err)
        self.assertIn("0001-alpha", err)
        self.assertIn("0001-beta", err)

    def test_show_not_found(self):
        _, err, rc = run_cli(["show", "9999"], cwd=self.tmpdir)
        self.assertEqual(rc, 3)
        self.assertIn("not found", err)

    def test_show_missing_task(self):
        _, err, rc = run_cli(["show", "0001-noexist"], cwd=self.tmpdir)
        self.assertEqual(rc, 3)
        self.assertIn("not found", err)


# ── Root Detection Tests ────────────────────────────────────────────


class TestRootDetection(unittest.TestCase):

    def test_source_repo_root(self):
        tmpdir = tempfile.mkdtemp()
        root = make_source_vault(tmpdir)
        make_task(root, "0001-alpha")

        out, _, rc = run_cli(["list"], cwd=tmpdir)
        self.assertEqual(rc, 0)
        self.assertIn("0001", out)

    def test_installed_project_root(self):
        tmpdir = tempfile.mkdtemp()
        root, os_dir = make_installed_vault(tmpdir)
        make_task(os_dir, "0001-alpha")

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

        # Installed markers with different task
        os_dir = root / ".openstation"
        (os_dir / "artifacts" / "tasks").mkdir(parents=True)

        make_task(root, "0001-source-task")
        make_task(os_dir, "0002-installed-task")

        out, _, rc = run_cli(["list", "--status", "all"], cwd=tmpdir)
        self.assertEqual(rc, 0)
        # Source repo takes precedence over .openstation/
        self.assertIn("0001", out)
        self.assertNotIn("0002", out)

    def test_child_directory_finds_root(self):
        tmpdir = tempfile.mkdtemp()
        root = make_source_vault(tmpdir)
        make_task(root, "0001-alpha")

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
        make_task(self.root, "0001-alpha", status="ready", agent="researcher")
        out, _, rc = run_cli(["run", "--task", "0001", "--dry-run"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertIn("claude", out)
        self.assertIn("--agent researcher", out)
        self.assertIn("0001-alpha", out)  # prompt references task name

    def test_by_task_full_slug(self):
        make_task(self.root, "0001-alpha", status="ready", agent="researcher")
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
        make_task(self.root, "0001-alpha", status="ready")
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
        make_task(self.root, "0001-alpha", status="in-progress", agent="researcher")
        _, stderr, rc = run_cli(
            ["run", "--task", "0001", "--dry-run"],
            cwd=self.tmpdir,
        )
        self.assertEqual(rc, 5)
        self.assertIn("has status 'in-progress'", stderr)
        self.assertIn("expected 'ready'", stderr)

    def test_task_not_ready_with_force(self):
        make_task(self.root, "0001-alpha", status="in-progress", agent="researcher")
        out, _, rc = run_cli(
            ["run", "--task", "0001", "--force", "--dry-run"],
            cwd=self.tmpdir,
        )
        self.assertEqual(rc, 0)
        self.assertIn("claude", out)

    def test_task_no_agent_assigned(self):
        make_task(self.root, "0001-alpha", status="ready", agent="")
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
        make_task(self.root, "0001-parent", status="ready", agent="researcher")
        out, stderr, rc = run_cli(
            ["run", "--task", "0001-parent", "--dry-run"],
            cwd=self.tmpdir,
        )
        self.assertEqual(rc, 0)
        self.assertIn("No subtasks found", stderr)
        self.assertIn("0001-parent", out)

    def test_subtask_discovery(self):
        # Create parent task with subtasks field
        make_task(self.root, "0001-parent", status="ready", agent="researcher",
                  subtasks=["0002-child"])
        # Create subtask
        make_task(self.root, "0002-child", status="ready", agent="researcher")

        out, stderr, rc = run_cli(
            ["run", "--task", "0001-parent", "--dry-run"],
            cwd=self.tmpdir,
        )
        self.assertEqual(rc, 0)
        self.assertIn("1 ready subtask", stderr)
        self.assertIn("0002-child", out)

    def test_max_tasks_limits_execution(self):
        # Create parent with two subtasks
        make_task(self.root, "0001-parent", status="ready", agent="researcher",
                  subtasks=["0002-child-a", "0003-child-b"])
        make_task(self.root, "0002-child-a", status="ready", agent="researcher")
        make_task(self.root, "0003-child-b", status="ready", agent="researcher")

        out, stderr, rc = run_cli(
            ["run", "--task", "0001-parent", "--max-tasks", "1", "--dry-run"],
            cwd=self.tmpdir,
        )
        self.assertEqual(rc, 0)
        self.assertIn("2 ready subtask", stderr)
        # Only first subtask should appear in dry-run output
        self.assertIn("0002-child-a", out)
        self.assertNotIn("0003-child-b", out)

    def test_subtask_wikilinks(self):
        # Subtasks listed as Obsidian wikilinks should resolve correctly
        make_task(self.root, "0001-parent", status="ready", agent="researcher",
                  subtasks=['"[[0002-child]]"'])
        make_task(self.root, "0002-child", status="ready", agent="researcher")

        out, stderr, rc = run_cli(
            ["run", "--task", "0001-parent", "--dry-run"],
            cwd=self.tmpdir,
        )
        self.assertEqual(rc, 0)
        self.assertIn("1 ready subtask", stderr)
        self.assertIn("0002-child", out)

    def test_subtask_only_ready_collected(self):
        make_task(self.root, "0001-parent", status="ready", agent="researcher",
                  subtasks=["0002-ready", "0003-done"])
        make_task(self.root, "0002-ready", status="ready", agent="researcher")
        make_task(self.root, "0003-done", status="done", agent="researcher")

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
        make_task(self.root, "0001-alpha", status="ready", agent="researcher")
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


# ── Agents Command Tests ─────────────────────────────────────────────


def make_agent_artifact(base, name, description=None, kind="agent", multiline=False):
    """Create an agent spec in artifacts/agents/."""
    agents_dir = base / "artifacts" / "agents"
    agents_dir.mkdir(parents=True, exist_ok=True)
    if multiline and description:
        desc_block = f"description: >-\n  {description}\n"
    elif description:
        desc_block = f"description: {description}\n"
    else:
        desc_block = "description: Test agent\n"
    (agents_dir / f"{name}.md").write_text(
        f"---\nkind: {kind}\nname: {name}\n{desc_block}"
        f"model: claude-sonnet-4-6\nallowed-tools:\n  - Read\n---\n\n# {name}\n"
    )


class TestAgentsCommand(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.root = make_source_vault(self.tmpdir)

    def test_agents_lists_all(self):
        make_agent_artifact(self.root, "researcher", "Research agent")
        make_agent_artifact(self.root, "author", "Content author")

        out, _, rc = run_cli(["agents"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertIn("researcher", out)
        self.assertIn("author", out)
        self.assertIn("Research agent", out)
        self.assertIn("Content author", out)

    def test_agents_includes_name_and_description_columns(self):
        make_agent_artifact(self.root, "developer", "Implements code")

        out, _, rc = run_cli(["agents"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertIn("Name", out)
        self.assertIn("Description", out)

    def test_agents_multiline_description(self):
        make_agent_artifact(self.root, "architect",
                           "Technical architect for designing systems",
                           multiline=True)

        out, _, rc = run_cli(["agents"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertIn("architect", out)
        self.assertIn("Technical architect for designing systems", out)

    def test_agents_skips_non_agent_files(self):
        make_agent_artifact(self.root, "researcher", "Research agent")
        # Create a non-agent file in artifacts/agents/
        agents_dir = self.root / "artifacts" / "agents"
        (agents_dir / "readme.md").write_text("# Not an agent\n")

        out, _, rc = run_cli(["agents"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertIn("researcher", out)
        self.assertNotIn("readme", out)

    def test_agents_empty_directory(self):
        out, _, rc = run_cli(["agents"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertEqual(out.strip(), "")

    def test_agents_sorted_by_name(self):
        make_agent_artifact(self.root, "zulu", "Last agent")
        make_agent_artifact(self.root, "alpha", "First agent")
        make_agent_artifact(self.root, "mid", "Middle agent")

        out, _, rc = run_cli(["agents"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        lines = [l for l in out.strip().splitlines() if l.strip() and not l.startswith("-")]
        data = lines[1:]  # skip header
        names = [l.split()[0] for l in data]
        self.assertEqual(names, ["alpha", "mid", "zulu"])

    def test_agents_installed_vault(self):
        tmpdir = tempfile.mkdtemp()
        root, os_dir = make_installed_vault(tmpdir)
        make_agent_artifact(os_dir, "researcher", "Research agent")

        out, _, rc = run_cli(["agents"], cwd=tmpdir)
        self.assertEqual(rc, 0)
        self.assertIn("researcher", out)


# ── Create Command Tests ─────────────────────────────────────────────


class TestCreateCommand(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.root = make_source_vault(self.tmpdir)

    def test_create_basic(self):
        out, _, rc = run_cli(["create", "my new task"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        task_name = out.strip()
        self.assertTrue(task_name.startswith("0001-"))
        # Verify file exists
        task_file = self.root / "artifacts" / "tasks" / f"{task_name}.md"
        self.assertTrue(task_file.exists())
        content = task_file.read_text()
        self.assertIn("kind: task", content)
        self.assertIn(f"name: {task_name}", content)
        self.assertIn("status: backlog", content)
        self.assertIn("owner: user", content)
        self.assertIn("# My New Task", content)
        self.assertIn("## Requirements", content)
        self.assertIn("## Verification", content)

    def test_create_sequential_ids(self):
        out1, _, rc1 = run_cli(["create", "first task"], cwd=self.tmpdir)
        self.assertEqual(rc1, 0)
        out2, _, rc2 = run_cli(["create", "second task"], cwd=self.tmpdir)
        self.assertEqual(rc2, 0)
        name1 = out1.strip()
        name2 = out2.strip()
        self.assertTrue(name1.startswith("0001-"))
        self.assertTrue(name2.startswith("0002-"))

    def test_create_with_existing_tasks(self):
        make_task(self.root, "0042-existing", status="done")
        out, _, rc = run_cli(["create", "new task"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertTrue(out.strip().startswith("0043-"))

    def test_create_slug_generation(self):
        out, _, rc = run_cli(["create", "Add Login Page!!"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        task_name = out.strip()
        self.assertIn("add-login-page", task_name)

    def test_create_slug_max_5_words(self):
        out, _, rc = run_cli(
            ["create", "one two three four five six seven"],
            cwd=self.tmpdir,
        )
        self.assertEqual(rc, 0)
        task_name = out.strip()
        # Slug should have at most 5 word-segments after the ID
        slug = task_name.split("-", 1)[1]  # remove NNNN-
        self.assertEqual(len(slug.split("-")), 5)

    def test_create_special_chars_stripped(self):
        out, _, rc = run_cli(["create", "fix #123 @urgent!"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        task_name = out.strip()
        # Should not contain special chars
        slug = task_name.split("-", 1)[1]
        self.assertTrue(re.match(r"^[a-z0-9-]+$", slug))

    def test_create_with_agent(self):
        out, _, rc = run_cli(
            ["create", "task with agent", "--agent", "researcher"],
            cwd=self.tmpdir,
        )
        self.assertEqual(rc, 0)
        task_name = out.strip()
        task_file = self.root / "artifacts" / "tasks" / f"{task_name}.md"
        content = task_file.read_text()
        self.assertIn("agent: researcher", content)

    def test_create_with_status_ready(self):
        out, _, rc = run_cli(
            ["create", "ready task", "--status", "ready"],
            cwd=self.tmpdir,
        )
        self.assertEqual(rc, 0)
        task_name = out.strip()
        task_file = self.root / "artifacts" / "tasks" / f"{task_name}.md"
        content = task_file.read_text()
        self.assertIn("status: ready", content)

    def test_create_invalid_status(self):
        _, stderr, rc = run_cli(
            ["create", "bad status", "--status", "done"],
            cwd=self.tmpdir,
        )
        self.assertEqual(rc, 1)
        self.assertIn("--status must be 'backlog' or 'ready'", stderr)

    def test_create_with_parent(self):
        make_task(self.root, "0001-parent-task", status="backlog")
        out, _, rc = run_cli(
            ["create", "child task", "--parent", "0001"],
            cwd=self.tmpdir,
        )
        self.assertEqual(rc, 0)
        task_name = out.strip()

        # Child has parent field
        child_file = self.root / "artifacts" / "tasks" / f"{task_name}.md"
        child_content = child_file.read_text()
        self.assertIn('parent: "[[0001-parent-task]]"', child_content)

        # Parent has subtasks field with child
        parent_file = self.root / "artifacts" / "tasks" / "0001-parent-task.md"
        parent_content = parent_file.read_text()
        self.assertIn(f"[[{task_name}]]", parent_content)
        self.assertIn("subtasks:", parent_content)

    def test_create_parent_already_has_subtasks(self):
        make_task(self.root, "0001-parent", status="backlog",
                  subtasks=['"[[0002-existing-child]]"'])
        make_task(self.root, "0002-existing-child", status="backlog")

        out, _, rc = run_cli(
            ["create", "new child", "--parent", "0001"],
            cwd=self.tmpdir,
        )
        self.assertEqual(rc, 0)
        task_name = out.strip()

        parent_file = self.root / "artifacts" / "tasks" / "0001-parent.md"
        parent_content = parent_file.read_text()
        # Both children should be listed
        self.assertIn("0002-existing-child", parent_content)
        self.assertIn(task_name, parent_content)

    def test_create_invalid_parent(self):
        _, stderr, rc = run_cli(
            ["create", "orphan task", "--parent", "9999-nonexistent"],
            cwd=self.tmpdir,
        )
        self.assertEqual(rc, 3)
        self.assertIn("parent task not found", stderr)

    def test_create_missing_description(self):
        _, stderr, rc = run_cli(["create"], cwd=self.tmpdir)
        self.assertNotEqual(rc, 0)

    def test_create_not_in_project(self):
        tmpdir = tempfile.mkdtemp()
        _, stderr, rc = run_cli(["create", "orphan"], cwd=tmpdir)
        self.assertEqual(rc, 2)
        self.assertIn("not in an Open Station project", stderr)


# ── Status Command Tests ─────────────────────────────────────────────


class TestStatusCommand(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.root = make_source_vault(self.tmpdir)

    def test_status_valid_transition(self):
        make_task(self.root, "0001-alpha", status="backlog")
        out, _, rc = run_cli(["status", "0001", "ready"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertIn("backlog → ready", out)

        # Verify file was updated
        task_file = self.root / "artifacts" / "tasks" / "0001-alpha.md"
        content = task_file.read_text()
        self.assertIn("status: ready", content)

    def test_status_all_valid_transitions(self):
        transitions = [
            ("backlog", "ready"),
            ("ready", "in-progress"),
            ("in-progress", "review"),
            ("review", "done"),
        ]
        for current, target in transitions:
            with self.subTest(transition=f"{current} → {target}"):
                tmpdir = tempfile.mkdtemp()
                root = make_source_vault(tmpdir)
                make_task(root, "0001-t", status=current)
                out, _, rc = run_cli(
                    ["status", "0001", target],
                    cwd=tmpdir,
                )
                self.assertEqual(rc, 0, f"Failed: {current} → {target}")

    def test_status_review_to_failed(self):
        make_task(self.root, "0001-alpha", status="review")
        out, _, rc = run_cli(["status", "0001", "failed"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertIn("review → failed", out)

    def test_status_failed_to_in_progress(self):
        make_task(self.root, "0001-alpha", status="failed")
        out, _, rc = run_cli(["status", "0001", "in-progress"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertIn("failed → in-progress", out)

    def test_status_invalid_transition(self):
        make_task(self.root, "0001-alpha", status="backlog")
        _, stderr, rc = run_cli(["status", "0001", "done"], cwd=self.tmpdir)
        self.assertEqual(rc, 5)
        self.assertIn("invalid transition", stderr)
        self.assertIn("allowed from backlog", stderr)

    def test_status_already_at_target(self):
        make_task(self.root, "0001-alpha", status="ready")
        out, _, rc = run_cli(["status", "0001", "ready"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertIn("already at ready", out)

    def test_status_task_not_found(self):
        _, stderr, rc = run_cli(["status", "9999", "ready"], cwd=self.tmpdir)
        self.assertEqual(rc, 3)
        self.assertIn("not found", stderr)

    def test_status_ambiguous_task(self):
        make_task(self.root, "0001-alpha", status="backlog")
        make_task(self.root, "0001-beta", status="backlog")
        _, stderr, rc = run_cli(["status", "0001", "ready"], cwd=self.tmpdir)
        self.assertEqual(rc, 4)
        self.assertIn("ambiguous", stderr)

    def test_status_preserves_file_content(self):
        make_task(self.root, "0001-alpha", status="backlog", agent="researcher")
        out, _, rc = run_cli(["status", "0001", "ready"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)

        task_file = self.root / "artifacts" / "tasks" / "0001-alpha.md"
        content = task_file.read_text()
        # Status changed
        self.assertIn("status: ready", content)
        # Other fields preserved
        self.assertIn("agent: researcher", content)
        self.assertIn("kind: task", content)
        self.assertIn("name: 0001-alpha", content)

    def test_status_not_in_project(self):
        tmpdir = tempfile.mkdtemp()
        _, stderr, rc = run_cli(["status", "0001", "ready"], cwd=tmpdir)
        self.assertEqual(rc, 2)
        self.assertIn("not in an Open Station project", stderr)

    def test_status_by_full_slug(self):
        make_task(self.root, "0001-alpha", status="backlog")
        out, _, rc = run_cli(["status", "0001-alpha", "ready"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertIn("backlog → ready", out)


if __name__ == "__main__":
    unittest.main()
