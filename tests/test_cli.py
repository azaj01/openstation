"""Integration tests for the OpenStation CLI (bin/openstation)."""

import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

CLI = str(Path(__file__).resolve().parent.parent / "bin" / "openstation")


def run_cli(args, cwd=None, env=None):
    """Run the CLI and return (stdout, stderr, returncode)."""
    result = subprocess.run(
        [sys.executable, CLI] + args,
        capture_output=True,
        text=True,
        cwd=cwd,
        env=env,
    )
    return result.stdout, result.stderr, result.returncode


def make_task(base, name, status="ready", assignee="researcher", owner="manual",
              subtasks=None, parent=None):
    """Create a minimal task fixture in the vault."""
    tasks_dir = base / "artifacts" / "tasks"
    tasks_dir.mkdir(parents=True, exist_ok=True)
    extra = ""
    if subtasks:
        extra = "subtasks:\n" + "".join(f"  - {s}\n" for s in subtasks)
    if parent:
        extra += f'parent: "[[{parent}]]"\n'
    (tasks_dir / f"{name}.md").write_text(
        f"---\nkind: task\nname: {name}\nstatus: {status}\n"
        f"assignee: {assignee}\nowner: {owner}\ncreated: 2026-01-01\n"
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

    def test_list_assignee_filter(self):
        make_task(self.root, "0001-alpha", assignee="researcher")
        make_task(self.root, "0002-beta", assignee="author")

        out, _, rc = run_cli(["list", "--assignee", "researcher"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertIn("0001", out)
        self.assertNotIn("0002", out)

    def test_list_combined_filters(self):
        make_task(self.root, "0001-alpha", status="ready", assignee="researcher")
        make_task(self.root, "0002-beta", status="in-progress", assignee="researcher")
        make_task(self.root, "0003-gamma", status="ready", assignee="author")

        out, _, rc = run_cli(["list", "--status", "ready", "--assignee", "researcher"], cwd=self.tmpdir)
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


# ── List Grouped Output Tests ──────────────────────────────────────


class TestListGroupedOutput(unittest.TestCase):
    """Test subtask grouping and Assignee column in list output."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.root = make_source_vault(self.tmpdir)

    def test_assignee_column_header(self):
        """Table header shows 'Assignee' instead of 'Agent'."""
        make_task(self.root, "0001-alpha", status="ready")
        out, _, rc = run_cli(["list"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        header_line = out.splitlines()[0]
        self.assertIn("Assignee", header_line)
        self.assertNotIn("Agent", header_line)

    def test_subtasks_grouped_under_parent(self):
        """Subtasks appear indented under their parent."""
        make_task(self.root, "0001-parent", status="ready", assignee="")
        make_task(self.root, "0002-child-a", status="ready", assignee="researcher",
                  parent="0001-parent")
        make_task(self.root, "0003-child-b", status="ready", assignee="author",
                  parent="0001-parent")

        out, _, rc = run_cli(["list"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        lines = out.strip().splitlines()
        parent_idx = next(i for i, l in enumerate(lines) if "0001-parent" in l)
        child_a_idx = next(i for i, l in enumerate(lines) if "0002-child-a" in l)
        child_b_idx = next(i for i, l in enumerate(lines) if "0003-child-b" in l)
        # Children appear after parent
        self.assertGreater(child_a_idx, parent_idx)
        self.assertGreater(child_b_idx, parent_idx)
        # Children have tree prefix in Name column, not ID column
        self.assertIn("\u2514\u2500", lines[child_a_idx])
        self.assertIn("\u2514\u2500", lines[child_b_idx])
        # Subtask IDs are still visible
        self.assertRegex(lines[child_a_idx], r"\b0002\b")
        self.assertRegex(lines[child_b_idx], r"\b0003\b")
        # Parent does NOT have tree prefix
        self.assertNotIn("\u2514\u2500", lines[parent_idx])

    def test_top_level_without_subtasks_unchanged(self):
        """Tasks without subtasks display as flat rows."""
        make_task(self.root, "0001-solo", status="ready")
        out, _, rc = run_cli(["list"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        data_lines = [l for l in out.strip().splitlines() if "0001" in l]
        self.assertEqual(len(data_lines), 1)
        self.assertNotIn("\u2514\u2500", data_lines[0])
        self.assertIn("0001", data_lines[0])

    def test_sorting_parents_by_id_subtasks_by_id(self):
        """Parents sorted by ID; subtasks sorted by ID within group."""
        make_task(self.root, "0010-parent-b", status="ready", assignee="")
        make_task(self.root, "0005-parent-a", status="ready", assignee="")
        make_task(self.root, "0012-child-b2", status="ready", assignee="",
                  parent="0010-parent-b")
        make_task(self.root, "0011-child-b1", status="ready", assignee="",
                  parent="0010-parent-b")

        out, _, rc = run_cli(["list"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        lines = [l for l in out.strip().splitlines()
                 if l.strip() and not l.startswith("-")]
        data = lines[1:]  # skip header
        expected_order = ["0005-parent-a", "0010-parent-b",
                          "0011-child-b1", "0012-child-b2"]
        found = []
        for l in data:
            for name in expected_order:
                if name in l:
                    found.append(name)
        self.assertEqual(found, expected_order)

    def test_pull_in_subtask_of_matching_parent(self):
        """Matching parent pulls in subtasks regardless of subtask status."""
        make_task(self.root, "0001-parent", status="ready", assignee="")
        make_task(self.root, "0002-child", status="done", assignee="researcher",
                  parent="0001-parent")

        out, _, rc = run_cli(["list", "--status", "ready"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertIn("0001-parent", out)
        self.assertIn("0002-child", out)  # pulled in despite status=done

    def test_orphan_subtask_shown_as_top_level(self):
        """Subtask whose parent is filtered out appears as top-level row."""
        make_task(self.root, "0001-parent", status="done", assignee="")
        make_task(self.root, "0002-child", status="ready", assignee="researcher",
                  parent="0001-parent")

        out, _, rc = run_cli(["list", "--status", "ready"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertNotIn("0001-parent", out)
        self.assertIn("0002-child", out)
        # Should appear as top-level (ID in normal position, no tree prefix)
        child_line = next(l for l in out.splitlines() if "0002-child" in l)
        self.assertNotIn("\u2514\u2500", child_line)
        self.assertTrue(child_line.strip().startswith("0002"))

    def test_assignee_filter_with_grouped_view(self):
        """Assignee filter works correctly with grouped subtasks."""
        make_task(self.root, "0001-parent", status="ready", assignee="researcher")
        make_task(self.root, "0002-child", status="ready", assignee="author",
                  parent="0001-parent")

        # Filter by author — parent filtered out, child becomes top-level
        out, _, rc = run_cli(["list", "--assignee", "author"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertNotIn("0001-parent", out)
        self.assertIn("0002-child", out)
        child_line = next(l for l in out.splitlines() if "0002-child" in l)
        self.assertNotIn("\u2514\u2500", child_line)

    def test_multi_level_nesting_flattened(self):
        """Grandchild tasks appear as subtasks alongside direct children."""
        make_task(self.root, "0001-root", status="ready", assignee="")
        make_task(self.root, "0002-child", status="ready", assignee="",
                  parent="0001-root")
        make_task(self.root, "0003-grandchild", status="ready", assignee="",
                  parent="0002-child")

        out, _, rc = run_cli(["list"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        lines = out.strip().splitlines()
        root_idx = next(i for i, l in enumerate(lines) if "0001-root" in l)
        child_idx = next(i for i, l in enumerate(lines) if "0002-child" in l)
        grandchild_idx = next(i for i, l in enumerate(lines) if "0003-grandchild" in l)
        # All descendants appear after root, in ID order
        self.assertGreater(child_idx, root_idx)
        self.assertGreater(grandchild_idx, child_idx)
        # Both child and grandchild have tree prefix
        self.assertIn("\u2514\u2500", lines[child_idx])
        self.assertIn("\u2514\u2500", lines[grandchild_idx])
        # Root does not
        self.assertNotIn("\u2514\u2500", lines[root_idx])


# ── List Pull-In and Positional Filter Tests ───────────────────────


class TestListPullIn(unittest.TestCase):
    """Test subtask pull-in rule: matching parents pull in all descendants."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.root = make_source_vault(self.tmpdir)

    def test_default_active_pulls_in_done_subtask(self):
        """Default active filter pulls in subtasks even if done/backlog/failed."""
        make_task(self.root, "0001-parent", status="ready", assignee="")
        make_task(self.root, "0002-child-done", status="done", assignee="",
                  parent="0001-parent")
        make_task(self.root, "0003-child-backlog", status="backlog", assignee="",
                  parent="0001-parent")
        make_task(self.root, "0004-child-failed", status="failed", assignee="",
                  parent="0001-parent")

        out, _, rc = run_cli(["list"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertIn("0001-parent", out)
        self.assertIn("0002-child-done", out)
        self.assertIn("0003-child-backlog", out)
        self.assertIn("0004-child-failed", out)

    def test_pull_in_nested_descendants(self):
        """Pull-in works recursively through grandchildren."""
        make_task(self.root, "0001-root", status="in-progress", assignee="")
        make_task(self.root, "0002-child", status="done", assignee="",
                  parent="0001-root")
        make_task(self.root, "0003-grandchild", status="backlog", assignee="",
                  parent="0002-child")

        out, _, rc = run_cli(["list"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertIn("0001-root", out)
        self.assertIn("0002-child", out)
        self.assertIn("0003-grandchild", out)

    def test_non_matching_top_level_still_excluded(self):
        """A top-level task that doesn't match filters is excluded."""
        make_task(self.root, "0001-matching", status="ready", assignee="")
        make_task(self.root, "0002-nonmatching", status="done", assignee="")

        out, _, rc = run_cli(["list"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertIn("0001-matching", out)
        self.assertNotIn("0002-nonmatching", out)

    def test_pull_in_with_assignee_filter(self):
        """Pull-in works with assignee filter too."""
        make_task(self.root, "0001-parent", status="ready", assignee="researcher")
        make_task(self.root, "0002-child", status="done", assignee="author",
                  parent="0001-parent")

        out, _, rc = run_cli(["list", "--assignee", "researcher"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertIn("0001-parent", out)
        self.assertIn("0002-child", out)  # pulled in despite different assignee

    def test_pulled_in_subtasks_display_with_prefix(self):
        """Pulled-in subtasks render with └─ prefix."""
        make_task(self.root, "0001-parent", status="review", assignee="")
        make_task(self.root, "0002-child", status="done", assignee="",
                  parent="0001-parent")

        out, _, rc = run_cli(["list"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        child_line = next(l for l in out.splitlines() if "0002-child" in l)
        self.assertIn("\u2514\u2500", child_line)


class TestListPositionalFilter(unittest.TestCase):
    """Test positional filter argument for list command."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.root = make_source_vault(self.tmpdir)

    def test_positional_task_id_shows_tree(self):
        """openstation list 0001 shows task and all subtasks."""
        make_task(self.root, "0001-parent", status="ready")
        make_task(self.root, "0002-child-a", status="done", parent="0001-parent")
        make_task(self.root, "0003-child-b", status="backlog", parent="0001-parent")
        make_task(self.root, "0004-unrelated", status="ready")

        out, _, rc = run_cli(["list", "0001"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertIn("0001-parent", out)
        self.assertIn("0002-child-a", out)
        self.assertIn("0003-child-b", out)
        self.assertNotIn("0004-unrelated", out)

    def test_positional_task_short_id(self):
        """Short ID works: openstation list 1."""
        make_task(self.root, "0001-parent", status="ready")
        make_task(self.root, "0002-child", status="done", parent="0001-parent")

        out, _, rc = run_cli(["list", "1"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertIn("0001-parent", out)
        self.assertIn("0002-child", out)

    def test_positional_task_with_status_flag(self):
        """Positional task filter combined with --status narrows results."""
        make_task(self.root, "0001-parent", status="ready")
        make_task(self.root, "0002-child-ready", status="ready", parent="0001-parent")
        make_task(self.root, "0003-child-done", status="done", parent="0001-parent")

        out, _, rc = run_cli(["list", "0001", "--status", "ready"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertIn("0001-parent", out)
        self.assertIn("0002-child-ready", out)
        # 0003 is pulled in because 0001-parent matches ready filter
        self.assertIn("0003-child-done", out)

    def test_positional_assignee_filter(self):
        """openstation list researcher filters by assignee."""
        make_task(self.root, "0001-alpha", status="ready", assignee="researcher")
        make_task(self.root, "0002-beta", status="ready", assignee="author")

        out, _, rc = run_cli(["list", "researcher"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertIn("0001-alpha", out)
        self.assertNotIn("0002-beta", out)

    def test_positional_assignee_same_as_flag(self):
        """Positional assignee gives same result as --assignee flag."""
        make_task(self.root, "0001-alpha", status="ready", assignee="author")
        make_task(self.root, "0002-beta", status="ready", assignee="developer")

        out1, _, rc1 = run_cli(["list", "author"], cwd=self.tmpdir)
        out2, _, rc2 = run_cli(["list", "--assignee", "author"], cwd=self.tmpdir)
        self.assertEqual(rc1, 0)
        self.assertEqual(rc2, 0)
        self.assertEqual(out1, out2)

    def test_positional_task_not_found(self):
        """Invalid task ID returns error."""
        _, stderr, rc = run_cli(["list", "9999"], cwd=self.tmpdir)
        self.assertEqual(rc, 3)
        self.assertIn("not found", stderr)

    def test_positional_filter_preserves_existing_flags(self):
        """Positional filter works with --status and --assignee flags."""
        make_task(self.root, "0001-alpha", status="ready", assignee="researcher")
        make_task(self.root, "0002-beta", status="in-progress", assignee="researcher")

        out, _, rc = run_cli(["list", "--status", "ready", "--assignee", "researcher"],
                             cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertIn("0001-alpha", out)
        self.assertNotIn("0002-beta", out)

    def test_positional_task_defaults_to_all_statuses(self):
        """Task filter defaults to --status all (shows every status)."""
        make_task(self.root, "0001-parent", status="done")
        make_task(self.root, "0002-child", status="backlog", parent="0001-parent")

        out, _, rc = run_cli(["list", "0001"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertIn("0001-parent", out)
        self.assertIn("0002-child", out)


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


# ── Flexible Task ID Resolution Tests ──────────────────────────────


class TestFlexibleTaskResolution(unittest.TestCase):
    """Test flexible task ID resolution: short IDs, slug-only lookup."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.root = make_source_vault(self.tmpdir)

    # --- Short ID (no leading zeros) ---

    def test_short_id_resolves(self):
        """'58' resolves to '0058-implement-foo'."""
        make_task(self.root, "0058-implement-foo")
        out, _, rc = run_cli(["show", "58"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertIn("0058-implement-foo", out)

    def test_short_id_single_digit(self):
        """'3' resolves to '0003-some-task'."""
        make_task(self.root, "0003-some-task")
        out, _, rc = run_cli(["show", "3"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertIn("0003-some-task", out)

    def test_short_id_two_digits(self):
        """'12' resolves to '0012-another-task'."""
        make_task(self.root, "0012-another-task")
        out, _, rc = run_cli(["show", "12"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertIn("0012-another-task", out)

    def test_zero_padded_id_still_works(self):
        """'0058' still resolves (existing behavior)."""
        make_task(self.root, "0058-implement-foo")
        out, _, rc = run_cli(["show", "0058"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertIn("0058-implement-foo", out)

    def test_full_name_still_works(self):
        """Full name exact match still works."""
        make_task(self.root, "0058-implement-foo")
        out, _, rc = run_cli(["show", "0058-implement-foo"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertIn("0058-implement-foo", out)

    # --- Slug-only lookup ---

    def test_slug_exact_resolves(self):
        """Exact slug 'implement-foo' resolves to '0058-implement-foo'."""
        make_task(self.root, "0058-implement-foo")
        out, _, rc = run_cli(["show", "implement-foo"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertIn("0058-implement-foo", out)

    def test_slug_prefix_resolves(self):
        """Slug prefix 'implement' resolves when unique."""
        make_task(self.root, "0058-implement-foo")
        out, _, rc = run_cli(["show", "implement"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertIn("0058-implement-foo", out)

    def test_slug_ambiguous_returns_error(self):
        """Ambiguous slug match returns error with candidates."""
        make_task(self.root, "0058-implement-foo")
        make_task(self.root, "0059-implement-bar")
        _, stderr, rc = run_cli(["show", "implement"], cwd=self.tmpdir)
        self.assertEqual(rc, 4)
        self.assertIn("ambiguous", stderr)
        self.assertIn("0058-implement-foo", stderr)
        self.assertIn("0059-implement-bar", stderr)

    def test_slug_not_found(self):
        """Non-matching slug returns not found."""
        make_task(self.root, "0058-implement-foo")
        _, stderr, rc = run_cli(["show", "nonexistent-slug"], cwd=self.tmpdir)
        self.assertEqual(rc, 3)
        self.assertIn("not found", stderr)

    # --- Resolution priority ---

    def test_exact_match_takes_priority(self):
        """Exact full name match wins over slug match."""
        # Create a task whose full name could also be a slug of another
        make_task(self.root, "0001-alpha")
        out, _, rc = run_cli(["show", "0001-alpha"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertIn("0001-alpha", out)

    def test_id_match_takes_priority_over_slug(self):
        """ID prefix match wins over slug match."""
        make_task(self.root, "0058-implement-foo")
        make_task(self.root, "0001-0058-confusing-name")
        # '0058' should match as ID prefix first, not as slug
        out, _, rc = run_cli(["show", "0058"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertIn("0058-implement-foo", out)

    # --- Works across subcommands ---

    def test_status_with_short_id(self):
        """Status command works with short ID."""
        make_task(self.root, "0058-implement-foo", status="backlog")
        out, _, rc = run_cli(["status", "58", "ready"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertIn("backlog → ready", out)

    def test_status_with_slug(self):
        """Status command works with slug-only lookup."""
        make_task(self.root, "0058-implement-foo", status="backlog")
        out, _, rc = run_cli(["status", "implement-foo", "ready"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertIn("backlog → ready", out)


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
        make_task(self.root, "0001-alpha", status="ready", assignee="researcher")
        out, _, rc = run_cli(["run", "--task", "0001", "--dry-run"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertIn("claude", out)
        self.assertIn("--agent researcher", out)
        self.assertIn("0001-alpha", out)  # prompt references task name

    def test_by_task_full_slug(self):
        make_task(self.root, "0001-alpha", status="ready", assignee="researcher")
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
        make_task(self.root, "0001-alpha", status="in-progress", assignee="researcher")
        _, stderr, rc = run_cli(
            ["run", "--task", "0001", "--dry-run"],
            cwd=self.tmpdir,
        )
        self.assertEqual(rc, 5)
        self.assertIn("has status 'in-progress'", stderr)
        self.assertIn("expected 'ready'", stderr)

    def test_task_not_ready_with_force(self):
        make_task(self.root, "0001-alpha", status="in-progress", assignee="researcher")
        out, _, rc = run_cli(
            ["run", "--task", "0001", "--force", "--dry-run"],
            cwd=self.tmpdir,
        )
        self.assertEqual(rc, 0)
        self.assertIn("claude", out)

    def test_task_no_agent_assigned(self):
        make_task(self.root, "0001-alpha", status="ready", assignee="")
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
        make_task(self.root, "0001-parent", status="ready", assignee="researcher")
        out, stderr, rc = run_cli(
            ["run", "--task", "0001-parent", "--dry-run"],
            cwd=self.tmpdir,
        )
        self.assertEqual(rc, 0)
        self.assertIn("No subtasks found", stderr)
        self.assertIn("0001-parent", out)

    def test_subtask_discovery(self):
        # Create parent task with subtasks field
        make_task(self.root, "0001-parent", status="ready", assignee="researcher",
                  subtasks=["0002-child"])
        # Create subtask
        make_task(self.root, "0002-child", status="ready", assignee="researcher")

        out, stderr, rc = run_cli(
            ["run", "--task", "0001-parent", "--dry-run"],
            cwd=self.tmpdir,
        )
        self.assertEqual(rc, 0)
        self.assertIn("1 ready subtask", stderr)
        self.assertIn("0002-child", out)

    def test_max_tasks_limits_execution(self):
        # Create parent with two subtasks
        make_task(self.root, "0001-parent", status="ready", assignee="researcher",
                  subtasks=["0002-child-a", "0003-child-b"])
        make_task(self.root, "0002-child-a", status="ready", assignee="researcher")
        make_task(self.root, "0003-child-b", status="ready", assignee="researcher")

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
        make_task(self.root, "0001-parent", status="ready", assignee="researcher",
                  subtasks=['"[[0002-child]]"'])
        make_task(self.root, "0002-child", status="ready", assignee="researcher")

        out, stderr, rc = run_cli(
            ["run", "--task", "0001-parent", "--dry-run"],
            cwd=self.tmpdir,
        )
        self.assertEqual(rc, 0)
        self.assertIn("1 ready subtask", stderr)
        self.assertIn("0002-child", out)

    def test_subtask_only_ready_collected(self):
        make_task(self.root, "0001-parent", status="ready", assignee="researcher",
                  subtasks=["0002-ready", "0003-done"])
        make_task(self.root, "0002-ready", status="ready", assignee="researcher")
        make_task(self.root, "0003-done", status="done", assignee="researcher")

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
        make_task(self.root, "0001-alpha", status="ready", assignee="researcher")
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

    def test_create_with_assignee(self):
        out, _, rc = run_cli(
            ["create", "task with assignee", "--assignee", "researcher"],
            cwd=self.tmpdir,
        )
        self.assertEqual(rc, 0)
        task_name = out.strip()
        task_file = self.root / "artifacts" / "tasks" / f"{task_name}.md"
        content = task_file.read_text()
        self.assertIn("assignee: researcher", content)

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
        make_task(self.root, "0001-alpha", status="backlog", assignee="researcher")
        out, _, rc = run_cli(["status", "0001", "ready"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)

        task_file = self.root / "artifacts" / "tasks" / "0001-alpha.md"
        content = task_file.read_text()
        # Status changed
        self.assertIn("status: ready", content)
        # Other fields preserved
        self.assertIn("assignee: researcher", content)
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


# ── Init Command Tests ──────────────────────────────────────────────


def make_local_source(tmpdir):
    """Create a minimal local source repo for --local mode."""
    src = Path(tmpdir) / "source"
    src.mkdir()
    # Source repo markers
    (src / "docs").mkdir(parents=True)
    (src / "docs" / "lifecycle.md").write_text("# Lifecycle\n")
    (src / "docs" / "task.spec.md").write_text("# Task Spec\n")
    (src / "commands").mkdir()
    for cmd in [
        "openstation.create.md", "openstation.dispatch.md",
        "openstation.done.md", "openstation.list.md",
        "openstation.ready.md", "openstation.reject.md",
        "openstation.show.md", "openstation.update.md",
    ]:
        (src / "commands" / cmd).write_text(f"# {cmd}\n")
    (src / "skills" / "openstation-execute").mkdir(parents=True)
    (src / "skills" / "openstation-execute" / "SKILL.md").write_text("# Skill\n")
    (src / "templates" / "agents").mkdir(parents=True)
    for agent in ["architect", "author", "developer", "project-manager", "researcher"]:
        (src / "templates" / "agents" / f"{agent}.md").write_text(
            f"---\nkind: agent\nname: {agent}\n"
            f"description: Agent for the project\n"
            f"allowed-tools:\n"
            f"  # --- Role-based (defined by agent template) ---\n"
            f"  - Read\n"
            f"  # --- Task-system (added by openstation) ---\n"
            f'  - "Bash(openstation *)"\n'
            f"---\n\n# {agent.title()}\n"
        )
    return str(src)


class TestInitCommand(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.target = Path(self.tmpdir) / "project"
        self.target.mkdir()
        self.local_src = make_local_source(self.tmpdir)
        # Set OPENSTATION_DIR so init reads from local source
        self.env = os.environ.copy()
        self.env["OPENSTATION_DIR"] = self.local_src

    def _run_init(self, extra_args=None):
        """Run init with OPENSTATION_DIR pointing to local source."""
        args = ["init"] + (extra_args or [])
        return run_cli(args, cwd=str(self.target), env=self.env)

    def test_first_init_creates_structure(self):
        """First init creates full .openstation/ directory tree."""
        out, _, rc = self._run_init()
        self.assertEqual(rc, 0, f"stdout: {out}")
        # Core directories exist
        self.assertTrue((self.target / ".openstation" / "docs").is_dir())
        self.assertTrue((self.target / ".openstation" / "artifacts" / "tasks").is_dir())
        self.assertTrue((self.target / ".openstation" / "agents").is_dir())
        self.assertTrue((self.target / ".openstation" / "commands").is_dir())
        self.assertTrue((self.target / ".openstation" / "skills").is_dir())
        self.assertTrue((self.target / ".claude").is_dir())

    def test_first_init_installs_commands(self):
        """AS-owned commands are installed."""
        self._run_init()
        cmd_file = self.target / ".openstation" / "commands" / "openstation.create.md"
        self.assertTrue(cmd_file.is_file())

    def test_first_init_installs_all_5_agents(self):
        """All 5 agent templates installed by default."""
        self._run_init()
        agents_dir = self.target / ".openstation" / "artifacts" / "agents"
        agents = sorted(p.stem for p in agents_dir.glob("*.md"))
        self.assertEqual(agents, ["architect", "author", "developer",
                                  "project-manager", "researcher"])

    def test_agent_templates_sourced_from_templates_dir(self):
        """Agent specs come from templates/agents/, not artifacts/agents/."""
        self._run_init()
        agent = (self.target / ".openstation" / "artifacts" / "agents" / "researcher.md")
        content = agent.read_text()
        self.assertIn("kind: agent", content)

    def test_agent_discovery_symlinks_created(self):
        """Each agent gets a discovery symlink in .openstation/agents/."""
        self._run_init()
        link = self.target / ".openstation" / "agents" / "researcher.md"
        self.assertTrue(link.is_symlink())
        self.assertEqual(os.readlink(str(link)), "../artifacts/agents/researcher.md")

    def test_claude_symlinks_created(self):
        """.claude/ directory symlinks point to .openstation/."""
        self._run_init()
        for name in ["commands", "agents", "skills"]:
            link = self.target / ".claude" / name
            self.assertTrue(link.is_symlink(), f".claude/{name} is not a symlink")

    def test_idempotent_reinit(self):
        """Second run doesn't break anything, user-owned files preserved."""
        self._run_init()
        # Modify a user-owned file
        agent_file = self.target / ".openstation" / "artifacts" / "agents" / "researcher.md"
        agent_file.write_text("# My custom agent\n")

        # Re-init
        out, _, rc = self._run_init()
        self.assertEqual(rc, 0)
        # User-owned file preserved
        self.assertEqual(agent_file.read_text(), "# My custom agent\n")
        # AS-owned file still updated
        cmd_file = self.target / ".openstation" / "commands" / "openstation.create.md"
        self.assertTrue(cmd_file.is_file())

    def test_reinit_with_force_overwrites_user_files(self):
        """--force overwrites user-owned agent specs."""
        self._run_init()
        agent_file = self.target / ".openstation" / "artifacts" / "agents" / "researcher.md"
        agent_file.write_text("# My custom agent\n")

        self._run_init(["--force"])
        # File overwritten
        self.assertNotEqual(agent_file.read_text(), "# My custom agent\n")
        self.assertIn("kind: agent", agent_file.read_text())

    def test_no_agents_flag(self):
        """--no-agents skips agent template installation."""
        self._run_init(["--no-agents"])
        agents_dir = self.target / ".openstation" / "artifacts" / "agents"
        agents = list(agents_dir.glob("*.md"))
        self.assertEqual(agents, [])

    def test_agents_filter_flag(self):
        """--agents selects specific agents."""
        self._run_init(["--agents", "researcher,author"])
        agents_dir = self.target / ".openstation" / "artifacts" / "agents"
        agents = sorted(p.stem for p in agents_dir.glob("*.md"))
        self.assertEqual(agents, ["author", "researcher"])

    def test_dry_run_no_files_created(self):
        """--dry-run doesn't create any files."""
        out, _, rc = self._run_init(["--dry-run"])
        self.assertEqual(rc, 0)
        self.assertFalse((self.target / ".openstation").is_dir())
        self.assertIn("[would]", out)

    def test_source_repo_guard(self):
        """Init refuses to run inside the source repo."""
        src_dir = Path(self.tmpdir) / "src_repo"
        src_dir.mkdir()
        (src_dir / "agents").mkdir()
        (src_dir / "install.sh").write_text("#!/bin/bash\n")

        _, stderr, rc = run_cli(["init"], cwd=str(src_dir), env=self.env)
        self.assertEqual(rc, 2)
        self.assertIn("Cannot init inside the Open Station source repo", stderr)

    def test_missing_install_gives_clear_error(self):
        """Init without prior install gives clear error message."""
        env = os.environ.copy()
        env["OPENSTATION_DIR"] = "/nonexistent/path"
        _, stderr, rc = run_cli(["init"], cwd=str(self.target), env=env)
        self.assertEqual(rc, 1)
        self.assertIn("openstation not installed", stderr)
        self.assertIn("curl", stderr)

    def test_bad_install_dir_gives_error(self):
        """Init with an invalid install dir (no docs/lifecycle.md) errors."""
        bad_path = Path(self.tmpdir) / "not_os"
        bad_path.mkdir()
        env = os.environ.copy()
        env["OPENSTATION_DIR"] = str(bad_path)

        _, stderr, rc = run_cli(["init"], cwd=str(self.target), env=env)
        self.assertEqual(rc, 1)
        self.assertIn("does not look like", stderr)

    def test_symlink_recreation(self):
        """Stale symlinks are corrected on re-init."""
        self._run_init()
        # Create a stale symlink
        link = self.target / ".claude" / "commands"
        if link.is_symlink():
            link.unlink()
        os.symlink("/nonexistent", str(link))

        # Re-init should fix it
        _, _, rc = self._run_init()
        self.assertEqual(rc, 0)
        self.assertTrue(link.is_symlink())
        self.assertTrue(link.resolve().is_dir() or not link.resolve().exists())
        # The symlink target should point to openstation
        self.assertIn(".openstation", os.readlink(str(link)))

    def test_not_git_repo_succeeds_with_warning(self):
        """Init succeeds with a warning when not in a git repo."""
        out, stderr, rc = self._run_init()
        self.assertEqual(rc, 0)
        self.assertIn("Not inside a git repository", stderr)

    def test_template_adaptation_strips_comment_markers(self):
        """Template comment markers are stripped from installed agents."""
        self._run_init()
        agent = self.target / ".openstation" / "artifacts" / "agents" / "researcher.md"
        content = agent.read_text()
        self.assertNotIn("# --- Role-based", content)
        self.assertNotIn("# --- Task-system", content)

    def test_gitkeep_files_created(self):
        """.gitkeep files are created in content directories."""
        self._run_init()
        gk = self.target / ".openstation" / "artifacts" / "tasks" / ".gitkeep"
        self.assertTrue(gk.is_file())

    def test_reinit_summary_message(self):
        """Re-init shows summary with file counts."""
        self._run_init()
        out, _, rc = self._run_init()
        self.assertEqual(rc, 0)
        self.assertIn("re-initialized", out)

    def test_first_init_summary_message(self):
        """First init shows success message with next steps."""
        out, _, rc = self._run_init()
        self.assertEqual(rc, 0)
        self.assertIn("initialized successfully", out)
        self.assertIn("Next steps", out)

    def test_mutual_exclusion_agents_no_agents(self):
        """--agents and --no-agents are mutually exclusive."""
        _, stderr, rc = self._run_init(["--agents", "researcher", "--no-agents"])
        self.assertNotEqual(rc, 0)


if __name__ == "__main__":
    unittest.main()
