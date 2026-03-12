"""Tests for the expanded agents subcommand (list, show)."""

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


def make_source_vault(tmpdir):
    """Create a source-repo-style vault."""
    root = Path(tmpdir)
    (root / "agents").mkdir(parents=True, exist_ok=True)
    (root / "install.sh").write_text("#!/bin/bash\n")
    (root / "artifacts" / "tasks").mkdir(parents=True, exist_ok=True)
    return root


def make_agent_artifact(base, name, description=None, kind="agent", multiline=False,
                        body=None):
    """Create an agent spec in artifacts/agents/."""
    agents_dir = base / "artifacts" / "agents"
    agents_dir.mkdir(parents=True, exist_ok=True)
    if multiline and description:
        desc_block = f"description: >-\n  {description}\n"
    elif description:
        desc_block = f"description: {description}\n"
    else:
        desc_block = "description: Test agent\n"
    body_text = body or f"# {name}\n\nAgent body text.\n"
    (agents_dir / f"{name}.md").write_text(
        f"---\nkind: {kind}\nname: {name}\n{desc_block}"
        f"model: claude-sonnet-4-6\nallowed-tools:\n  - Read\n---\n\n{body_text}"
    )


# ── agents list ──────────────────────────────────────────────────────


class TestAgentsList(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.root = make_source_vault(self.tmpdir)

    def test_bare_agents_lists_all(self):
        """Bare 'agents' (no sub-action) lists agents — backward compat."""
        make_agent_artifact(self.root, "researcher", "Research agent")
        make_agent_artifact(self.root, "author", "Content author")

        out, _, rc = run_cli(["agents"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertIn("researcher", out)
        self.assertIn("author", out)

    def test_agents_list_explicit(self):
        """'agents list' produces same output as bare 'agents'."""
        make_agent_artifact(self.root, "researcher", "Research agent")

        out_bare, _, rc_bare = run_cli(["agents"], cwd=self.tmpdir)
        out_list, _, rc_list = run_cli(["agents", "list"], cwd=self.tmpdir)
        self.assertEqual(rc_bare, 0)
        self.assertEqual(rc_list, 0)
        self.assertEqual(out_bare, out_list)

    def test_agents_list_json(self):
        make_agent_artifact(self.root, "researcher", "Research agent")
        make_agent_artifact(self.root, "author", "Content author")

        out, _, rc = run_cli(["agents", "list", "--json"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        data = json.loads(out)
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 2)
        names = [a["name"] for a in data]
        self.assertIn("researcher", names)
        self.assertIn("author", names)

    def test_agents_list_json_short_flag(self):
        make_agent_artifact(self.root, "researcher", "Research agent")

        out, _, rc = run_cli(["agents", "list", "-j"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        data = json.loads(out)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["name"], "researcher")

    def test_agents_list_quiet(self):
        make_agent_artifact(self.root, "researcher", "Research agent")
        make_agent_artifact(self.root, "author", "Content author")

        out, _, rc = run_cli(["agents", "list", "--quiet"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        lines = out.strip().splitlines()
        self.assertEqual(sorted(lines), ["author", "researcher"])
        # No header in quiet mode
        self.assertNotIn("Name", out)

    def test_agents_list_quiet_short_flag(self):
        make_agent_artifact(self.root, "researcher", "Research agent")

        out, _, rc = run_cli(["agents", "list", "-q"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertEqual(out.strip(), "researcher")

    def test_agents_list_empty(self):
        out, _, rc = run_cli(["agents", "list"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertEqual(out.strip(), "")

    def test_agents_list_json_empty(self):
        out, _, rc = run_cli(["agents", "list", "--json"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        data = json.loads(out)
        self.assertEqual(data, [])

    def test_agents_list_sorted(self):
        make_agent_artifact(self.root, "zulu", "Last")
        make_agent_artifact(self.root, "alpha", "First")

        out, _, rc = run_cli(["agents", "list", "-q"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        names = out.strip().splitlines()
        self.assertEqual(names, ["alpha", "zulu"])


# ── agents show ──────────────────────────────────────────────────────


class TestAgentsShow(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.root = make_source_vault(self.tmpdir)

    def test_show_prints_full_spec(self):
        make_agent_artifact(self.root, "researcher", "Research agent",
                            body="# Researcher\n\nFull body text here.\n")

        out, _, rc = run_cli(["agents", "show", "researcher"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertIn("kind: agent", out)
        self.assertIn("name: researcher", out)
        self.assertIn("Full body text here.", out)

    def test_show_json(self):
        make_agent_artifact(self.root, "researcher", "Research agent",
                            body="# Researcher\n\nBody content.\n")

        out, _, rc = run_cli(["agents", "show", "researcher", "--json"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        data = json.loads(out)
        self.assertEqual(data["name"], "researcher")
        self.assertEqual(data["kind"], "agent")
        self.assertIn("Body content.", data["body"])

    def test_show_json_short_flag(self):
        make_agent_artifact(self.root, "researcher", "Research agent")

        out, _, rc = run_cli(["agents", "show", "researcher", "-j"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        data = json.loads(out)
        self.assertEqual(data["name"], "researcher")

    def test_show_not_found(self):
        make_agent_artifact(self.root, "researcher", "Research agent")

        out, err, rc = run_cli(["agents", "show", "nonexistent"], cwd=self.tmpdir)
        self.assertEqual(rc, 3)  # EXIT_NOT_FOUND
        self.assertIn("not found", err.lower())
        self.assertIn("researcher", err)  # hint lists available

    def test_show_not_found_no_agents(self):
        _, err, rc = run_cli(["agents", "show", "nonexistent"], cwd=self.tmpdir)
        self.assertEqual(rc, 3)
        self.assertIn("not found", err.lower())


# ── agents help ──────────────────────────────────────────────────────


class TestAgentsHelp(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.root = make_source_vault(self.tmpdir)

    def test_agents_help(self):
        out, _, rc = run_cli(["agents", "--help"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertIn("list", out)
        self.assertIn("show", out)
        self.assertNotIn("dispatch", out)


# ── ag alias ─────────────────────────────────────────────────────────


class TestAgAlias(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.root = make_source_vault(self.tmpdir)

    def test_ag_list(self):
        """'ag list' works as alias for 'agents list'."""
        make_agent_artifact(self.root, "researcher", "Research agent")

        out_agents, _, rc_agents = run_cli(["agents", "list", "-q"], cwd=self.tmpdir)
        out_ag, _, rc_ag = run_cli(["ag", "list", "-q"], cwd=self.tmpdir)
        self.assertEqual(rc_agents, 0)
        self.assertEqual(rc_ag, 0)
        self.assertEqual(out_agents, out_ag)

    def test_ag_bare(self):
        """Bare 'ag' (no sub-action) lists agents."""
        make_agent_artifact(self.root, "author", "Content author")

        out, _, rc = run_cli(["ag"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertIn("author", out)

    def test_ag_show(self):
        """'ag show <name>' works."""
        make_agent_artifact(self.root, "researcher", "Research agent",
                            body="# Researcher\n\nBody.\n")

        out, _, rc = run_cli(["ag", "show", "researcher"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertIn("name: researcher", out)

if __name__ == "__main__":
    unittest.main()
