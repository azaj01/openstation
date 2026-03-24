"""Tests for allowed-tools merging, --tools flag, and tool-stall detection."""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SRC_DIR = str(Path(__file__).resolve().parent.parent / "src")


def run_cli(args, cwd=None, env=None):
    """Run the CLI and return (stdout, stderr, returncode)."""
    run_env = dict(env or os.environ)
    existing = run_env.get("PYTHONPATH", "")
    run_env["PYTHONPATH"] = SRC_DIR + (os.pathsep + existing if existing else "")
    result = subprocess.run(
        [sys.executable, "-m", "openstation"] + args,
        capture_output=True,
        text=True,
        cwd=cwd,
        env=run_env,
    )
    return result.stdout, result.stderr, result.returncode


_GIT_ENV = {
    **os.environ,
    "GIT_AUTHOR_NAME": "test", "GIT_AUTHOR_EMAIL": "t@t",
    "GIT_COMMITTER_NAME": "test", "GIT_COMMITTER_EMAIL": "t@t",
}


def make_source_vault(tmpdir):
    root = Path(tmpdir)
    subprocess.run(["git", "init"], cwd=str(root), capture_output=True, check=True)
    subprocess.run(
        ["git", "commit", "--allow-empty", "-m", "init"],
        cwd=str(root), capture_output=True, check=True, env=_GIT_ENV,
    )
    (root / ".openstation" / "agents").mkdir(parents=True, exist_ok=True)
    (root / ".openstation" / "artifacts" / "tasks").mkdir(parents=True, exist_ok=True)
    return root


def make_agent_spec(base, name, tools=None):
    if tools is None:
        tools = ["Read", "Glob", "Grep"]
    agents_dir = base / ".openstation" / "agents"
    agents_dir.mkdir(parents=True, exist_ok=True)
    tool_lines = "\n".join(f"  - {t}" for t in tools)
    (agents_dir / f"{name}.md").write_text(
        f"---\nkind: agent\nname: {name}\n"
        f"description: Test agent\nmodel: claude-sonnet-4-6\n"
        f"allowed-tools:\n{tool_lines}\n---\n\n# {name}\n"
    )


def make_task(base, name, status="ready", assignee="researcher", allowed_tools=None):
    tasks_dir = base / ".openstation" / "artifacts" / "tasks"
    tasks_dir.mkdir(parents=True, exist_ok=True)
    extra = ""
    if allowed_tools:
        extra = "allowed-tools:\n" + "".join(f"  - {t}\n" for t in allowed_tools)
    (tasks_dir / f"{name}.md").write_text(
        f"---\nkind: task\nname: {name}\nstatus: {status}\n"
        f"assignee: {assignee}\nowner: user\ncreated: 2026-01-01\n"
        f"{extra}---\n\n# {name}\n"
    )


# ---------------------------------------------------------------------------
# Unit tests for merge_tools
# ---------------------------------------------------------------------------

class TestMergeTools(unittest.TestCase):
    def setUp(self):
        # Import after PYTHONPATH setup isn't needed for unit tests
        sys.path.insert(0, SRC_DIR)
        from openstation.run import merge_tools
        self.merge_tools = merge_tools

    def test_single_list(self):
        result = self.merge_tools(["Read", "Glob"])
        self.assertEqual(result, ["Read", "Glob"])

    def test_merge_two_lists(self):
        result = self.merge_tools(["Read", "Glob"], ["Write", "Edit"])
        self.assertEqual(result, ["Read", "Glob", "Write", "Edit"])

    def test_dedup_preserves_order(self):
        result = self.merge_tools(["Read", "Glob"], ["Glob", "Write"])
        self.assertEqual(result, ["Read", "Glob", "Write"])

    def test_three_lists_priority(self):
        """Later lists add after earlier ones, dedup removes repeats."""
        result = self.merge_tools(
            ["Read", "Glob"],       # agent
            ["Glob", "Write"],      # task
            ["Write", "WebFetch"],  # CLI
        )
        self.assertEqual(result, ["Read", "Glob", "Write", "WebFetch"])

    def test_empty_lists(self):
        result = self.merge_tools([], [], [])
        self.assertEqual(result, [])

    def test_empty_middle_list(self):
        result = self.merge_tools(["Read"], [], ["Write"])
        self.assertEqual(result, ["Read", "Write"])


# ---------------------------------------------------------------------------
# Unit tests for detect_tool_stall
# ---------------------------------------------------------------------------

class TestDetectToolStall(unittest.TestCase):
    def setUp(self):
        sys.path.insert(0, SRC_DIR)
        from openstation.run import detect_tool_stall
        self.detect_tool_stall = detect_tool_stall

    def test_no_stall_on_none(self):
        self.assertFalse(self.detect_tool_stall(None))

    def test_no_stall_on_empty(self):
        self.assertFalse(self.detect_tool_stall(""))

    def test_no_stall_on_normal_text(self):
        self.assertFalse(self.detect_tool_stall("Task completed successfully."))

    def test_detects_approve_the_tool(self):
        self.assertTrue(self.detect_tool_stall(
            "I need you to approve the tool before I can continue."
        ))

    def test_detects_need_your_approval(self):
        self.assertTrue(self.detect_tool_stall(
            "I need your approval to use the Bash tool."
        ))

    def test_detects_approve_tool_permissions(self):
        self.assertTrue(self.detect_tool_stall(
            "Please approve tool permissions for this session."
        ))

    def test_detects_please_approve(self):
        self.assertTrue(self.detect_tool_stall(
            "Please approve the Write tool so I can create the file."
        ))

    def test_detects_requires_permission(self):
        self.assertTrue(self.detect_tool_stall(
            "This action requires your permission to proceed."
        ))

    def test_case_insensitive(self):
        self.assertTrue(self.detect_tool_stall(
            "PLEASE APPROVE THE TOOL"
        ))


# ---------------------------------------------------------------------------
# CLI integration tests for task allowed-tools merge
# ---------------------------------------------------------------------------

class TestTaskAllowedToolsMerge(unittest.TestCase):
    """Task-level allowed-tools are merged with agent tools in dry-run output."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.root = make_source_vault(self.tmpdir)
        make_agent_spec(self.root, "researcher", tools=["Read", "Glob", "Grep"])

    def test_task_tools_appear_in_command(self):
        make_task(self.root, "0001-alpha", allowed_tools=["Write", "WebFetch"])
        out, _, rc = run_cli(
            ["run", "--task", "0001", "--dry-run"],
            cwd=self.tmpdir,
        )
        self.assertEqual(rc, 0)
        self.assertIn("Read", out)
        self.assertIn("Write", out)
        self.assertIn("WebFetch", out)

    def test_task_tools_dedup_with_agent(self):
        """Duplicate tools between agent and task are not repeated."""
        make_task(self.root, "0001-alpha", allowed_tools=["Read", "Write"])
        out, _, rc = run_cli(
            ["run", "--task", "0001", "--dry-run", "--json"],
            cwd=self.tmpdir,
        )
        self.assertEqual(rc, 0)
        data = json.loads(out)
        cmd = data["command"]
        # Find tools after --allowedTools flag
        idx = cmd.index("--allowedTools")
        # Tools follow --allowedTools until the next flag or end
        tools_in_cmd = []
        for item in cmd[idx + 1:]:
            if item.startswith("-"):
                break
            tools_in_cmd.append(item)
        self.assertEqual(tools_in_cmd.count("Read"), 1, "Read should appear exactly once")
        self.assertIn("Write", tools_in_cmd)

    def test_no_task_tools_backward_compat(self):
        """Tasks without allowed-tools work as before."""
        make_task(self.root, "0001-alpha")
        out, _, rc = run_cli(
            ["run", "--task", "0001", "--dry-run"],
            cwd=self.tmpdir,
        )
        self.assertEqual(rc, 0)
        self.assertIn("Read", out)
        self.assertIn("Glob", out)
        self.assertIn("Grep", out)


# ---------------------------------------------------------------------------
# CLI integration tests for --tools flag
# ---------------------------------------------------------------------------

class TestCliToolsFlag(unittest.TestCase):
    """--tools flag appends extra tools to the merged list."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.root = make_source_vault(self.tmpdir)
        make_agent_spec(self.root, "researcher", tools=["Read", "Glob"])

    def test_tools_flag_by_agent(self):
        out, _, rc = run_cli(
            ["run", "researcher", "--dry-run", "--tools", "Write", "Edit"],
            cwd=self.tmpdir,
        )
        self.assertEqual(rc, 0)
        self.assertIn("Read", out)
        self.assertIn("Glob", out)
        self.assertIn("Write", out)
        self.assertIn("Edit", out)

    def test_tools_flag_by_task(self):
        make_task(self.root, "0001-alpha")
        out, _, rc = run_cli(
            ["run", "--task", "0001", "--dry-run", "--tools", "WebFetch"],
            cwd=self.tmpdir,
        )
        self.assertEqual(rc, 0)
        self.assertIn("WebFetch", out)

    def test_tools_flag_dedup(self):
        """--tools deduplicates with agent tools."""
        out, _, rc = run_cli(
            ["run", "researcher", "--dry-run", "--tools", "Read", "Write"],
            cwd=self.tmpdir,
        )
        self.assertEqual(rc, 0)
        parts = out.split()
        read_count = parts.count("Read")
        self.assertEqual(read_count, 1, f"Read appeared {read_count} times")
        self.assertIn("Write", out)

    def test_all_three_sources_merge(self):
        """Agent + task + CLI tools all merge with dedup."""
        make_task(self.root, "0001-alpha", allowed_tools=["Write"])
        out, _, rc = run_cli(
            ["run", "--task", "0001", "--dry-run", "--tools", "WebFetch"],
            cwd=self.tmpdir,
        )
        self.assertEqual(rc, 0)
        self.assertIn("Read", out)    # agent
        self.assertIn("Write", out)   # task
        self.assertIn("WebFetch", out)  # CLI


if __name__ == "__main__":
    unittest.main()
