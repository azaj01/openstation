"""Tests for the artifacts subcommand (list, show)."""

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


def make_artifact(base, kind, name, description=None, body=None, fm_kind=None):
    """Create an artifact in artifacts/<kind>/."""
    subdir = base / "artifacts" / kind
    subdir.mkdir(parents=True, exist_ok=True)
    fm_kind_val = fm_kind or kind.rstrip("s") if kind != "agents" else "agent"
    if kind == "agents":
        fm_kind_val = "agent"
    elif kind == "research":
        fm_kind_val = "research"
    elif kind == "specs":
        fm_kind_val = "spec"
    desc_line = f"description: {description}\n" if description else ""
    body_text = body or f"# {name}\n\nBody text.\n"
    (subdir / f"{name}.md").write_text(
        f"---\nkind: {fm_kind_val}\nname: {name}\n{desc_line}---\n\n{body_text}"
    )


# ── artifacts list ──────────────────────────────────────────────────


class TestArtifactsList(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.root = make_source_vault(self.tmpdir)

    def test_bare_artifacts_lists_all_non_tasks(self):
        """Bare 'artifacts' lists agents, research, specs."""
        make_artifact(self.root, "agents", "researcher", "Research agent")
        make_artifact(self.root, "research", "my-research", "Research output")
        make_artifact(self.root, "specs", "my-spec", "A specification")

        out, _, rc = run_cli(["artifacts"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertIn("researcher", out)
        self.assertIn("my-research", out)
        self.assertIn("my-spec", out)

    def test_artifacts_list_explicit(self):
        """'artifacts list' produces same output as bare 'artifacts'."""
        make_artifact(self.root, "research", "my-research", "Research output")

        out_bare, _, rc_bare = run_cli(["artifacts"], cwd=self.tmpdir)
        out_list, _, rc_list = run_cli(["artifacts", "list"], cwd=self.tmpdir)
        self.assertEqual(rc_bare, 0)
        self.assertEqual(rc_list, 0)
        self.assertEqual(out_bare, out_list)

    def test_artifacts_list_kind_filter(self):
        """--kind filters to a single subdirectory."""
        make_artifact(self.root, "agents", "researcher", "Research agent")
        make_artifact(self.root, "research", "my-research", "Research output")

        out, _, rc = run_cli(["artifacts", "list", "--kind", "research"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertIn("my-research", out)
        self.assertNotIn("researcher", out)

    def test_artifacts_list_kind_agents(self):
        make_artifact(self.root, "agents", "author", "Content author")
        make_artifact(self.root, "research", "my-research", "Research output")

        out, _, rc = run_cli(["artifacts", "list", "--kind", "agents"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertIn("author", out)
        self.assertNotIn("my-research", out)

    def test_artifacts_list_json(self):
        make_artifact(self.root, "research", "my-research", "Research output")
        make_artifact(self.root, "specs", "my-spec", "A specification")

        out, _, rc = run_cli(["artifacts", "list", "--json"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        data = json.loads(out)
        self.assertIsInstance(data, list)
        names = [a["name"] for a in data]
        self.assertIn("my-research", names)
        self.assertIn("my-spec", names)
        # Each entry has name, kind, summary
        for item in data:
            self.assertIn("name", item)
            self.assertIn("kind", item)
            self.assertIn("summary", item)

    def test_artifacts_list_json_short_flag(self):
        make_artifact(self.root, "research", "my-research", "Research output")

        out, _, rc = run_cli(["artifacts", "list", "-j"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        data = json.loads(out)
        self.assertEqual(len(data), 1)

    def test_artifacts_list_quiet(self):
        make_artifact(self.root, "research", "my-research", "Research output")
        make_artifact(self.root, "specs", "my-spec", "A specification")

        out, _, rc = run_cli(["artifacts", "list", "--quiet"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        lines = out.strip().splitlines()
        self.assertIn("my-research", lines)
        self.assertIn("my-spec", lines)
        # No header in quiet mode
        self.assertNotIn("Name", out)

    def test_artifacts_list_quiet_short_flag(self):
        make_artifact(self.root, "research", "my-research", "Research output")

        out, _, rc = run_cli(["artifacts", "list", "-q"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertEqual(out.strip(), "my-research")

    def test_artifacts_list_empty(self):
        out, _, rc = run_cli(["artifacts", "list"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertEqual(out.strip(), "")

    def test_artifacts_list_json_empty(self):
        out, _, rc = run_cli(["artifacts", "list", "--json"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        data = json.loads(out)
        self.assertEqual(data, [])

    def test_artifacts_list_sorted_by_kind_then_name(self):
        make_artifact(self.root, "specs", "zulu-spec", "Last")
        make_artifact(self.root, "agents", "alpha-agent", "First")

        out, _, rc = run_cli(["artifacts", "list", "-q"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        names = out.strip().splitlines()
        # agents before specs (sorted by kind)
        self.assertEqual(names[0], "alpha-agent")
        self.assertEqual(names[1], "zulu-spec")

    def test_artifacts_list_kind_tasks_rejected(self):
        """--kind tasks is rejected with a helpful message."""
        _, err, rc = run_cli(["artifacts", "list", "--kind", "tasks"], cwd=self.tmpdir)
        self.assertNotEqual(rc, 0)
        self.assertIn("openstation list", err)

    def test_artifacts_list_unknown_kind(self):
        _, err, rc = run_cli(["artifacts", "list", "--kind", "unknown"], cwd=self.tmpdir)
        self.assertNotEqual(rc, 0)
        self.assertIn("unknown artifact kind", err)


# ── artifacts show ──────────────────────────────────────────────────


class TestArtifactsShow(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.root = make_source_vault(self.tmpdir)

    def test_show_prints_full_content(self):
        make_artifact(self.root, "research", "my-research", "Research output",
                      body="# My Research\n\nDetailed findings here.\n")

        out, _, rc = run_cli(["artifacts", "show", "my-research"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertIn("kind: research", out)
        self.assertIn("Detailed findings here.", out)

    def test_show_json(self):
        make_artifact(self.root, "specs", "my-spec", "A specification",
                      body="# My Spec\n\nSpec body.\n")

        out, _, rc = run_cli(["artifacts", "show", "my-spec", "--json"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        data = json.loads(out)
        self.assertEqual(data["name"], "my-spec")
        self.assertIn("Spec body.", data["body"])

    def test_show_json_short_flag(self):
        make_artifact(self.root, "specs", "my-spec", "A specification")

        out, _, rc = run_cli(["artifacts", "show", "my-spec", "-j"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        data = json.loads(out)
        self.assertEqual(data["name"], "my-spec")

    def test_show_not_found(self):
        make_artifact(self.root, "research", "my-research", "Research output")

        _, err, rc = run_cli(["artifacts", "show", "nonexistent"], cwd=self.tmpdir)
        self.assertEqual(rc, 3)  # EXIT_NOT_FOUND
        self.assertIn("not found", err.lower())

    def test_show_resolves_across_directories(self):
        """Name resolution works across research/, specs/, agents/."""
        make_artifact(self.root, "specs", "unique-spec", "A spec")

        out, _, rc = run_cli(["artifacts", "show", "unique-spec"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertIn("kind: spec", out)

    def test_show_ambiguous_produces_error(self):
        """Ambiguous name lists candidates."""
        make_artifact(self.root, "research", "shared-name", "In research")
        make_artifact(self.root, "specs", "shared-name", "In specs")

        _, err, rc = run_cli(["artifacts", "show", "shared-name"], cwd=self.tmpdir)
        self.assertEqual(rc, 4)  # EXIT_AMBIGUOUS
        self.assertIn("ambiguous", err.lower())
        self.assertIn("research", err)
        self.assertIn("specs", err)

    def test_show_partial_match(self):
        """Partial name matches work when unambiguous."""
        make_artifact(self.root, "research", "cli-feature-research", "CLI research")

        out, _, rc = run_cli(["artifacts", "show", "cli-feature-research"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertIn("cli-feature-research", out)


# ── art alias ───────────────────────────────────────────────────────


class TestArtAlias(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.root = make_source_vault(self.tmpdir)

    def test_art_list(self):
        """'art list' works as alias for 'artifacts list'."""
        make_artifact(self.root, "research", "my-research", "Research output")

        out_full, _, rc_full = run_cli(["artifacts", "list", "-q"], cwd=self.tmpdir)
        out_alias, _, rc_alias = run_cli(["art", "list", "-q"], cwd=self.tmpdir)
        self.assertEqual(rc_full, 0)
        self.assertEqual(rc_alias, 0)
        self.assertEqual(out_full, out_alias)

    def test_art_bare(self):
        """Bare 'art' lists artifacts."""
        make_artifact(self.root, "specs", "my-spec", "A specification")

        out, _, rc = run_cli(["art"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertIn("my-spec", out)

    def test_art_show(self):
        """'art show <name>' works."""
        make_artifact(self.root, "research", "my-research", "Research output",
                      body="# Research\n\nBody.\n")

        out, _, rc = run_cli(["art", "show", "my-research"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertIn("name: my-research", out)


if __name__ == "__main__":
    unittest.main()
