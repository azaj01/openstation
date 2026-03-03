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


if __name__ == "__main__":
    unittest.main()
