"""Tests for the suspend hook (bin/hooks/suspend)."""

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SRC_DIR = str(Path(__file__).resolve().parent.parent / "src")
HOOK_PATH = str(Path(__file__).resolve().parent.parent / "bin" / "hooks" / "suspend")

_GIT_ENV = {
    **os.environ,
    "GIT_AUTHOR_NAME": "test", "GIT_AUTHOR_EMAIL": "t@t",
    "GIT_COMMITTER_NAME": "test", "GIT_COMMITTER_EMAIL": "t@t",
}


def _make_git_repo(tmpdir):
    """Initialize a git repo with an initial commit."""
    subprocess.run(["git", "init"], cwd=str(tmpdir), capture_output=True, check=True)
    subprocess.run(
        ["git", "commit", "--allow-empty", "-m", "init"],
        cwd=str(tmpdir), capture_output=True, check=True, env=_GIT_ENV,
    )


def _run_hook(env, cwd, stdin_text="n\n"):
    """Run the suspend hook with the given env and return (stdout, stderr, rc)."""
    result = subprocess.run(
        ["bash", HOOK_PATH],
        capture_output=True,
        text=True,
        cwd=str(cwd),
        env=env,
        input=stdin_text,
    )
    return result.stdout, result.stderr, result.returncode


class TestSuspendHookSectionAppend(unittest.TestCase):
    """Test that the suspend hook appends ## Suspended sections correctly."""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        _make_git_repo(self.tmpdir)
        self.task_file = self.tmpdir / "task.md"

    def _env(self, new_status="ready"):
        return {
            **_GIT_ENV,
            "OS_TASK_NAME": "0042-test-task",
            "OS_TASK_FILE": str(self.task_file),
            "OS_VAULT_ROOT": str(self.tmpdir),
            "OS_OLD_STATUS": "in-progress",
            "OS_NEW_STATUS": new_status,
            "PATH": os.environ.get("PATH", ""),
        }

    def test_appends_suspended_section_before_verification(self):
        self.task_file.write_text(
            "---\nkind: task\nname: 0042-test-task\nstatus: ready\n---\n\n"
            "# Test Task\n\n## Requirements\n\nDo stuff.\n\n## Verification\n\n- [ ] done\n"
        )
        stdout, stderr, rc = _run_hook(self._env(), self.tmpdir, stdin_text="\nn\n")
        self.assertEqual(rc, 0, f"Hook failed: {stderr}")
        content = self.task_file.read_text()
        self.assertIn("## Suspended", content)
        self.assertIn("**Target:** ready", content)
        # Suspended should appear before Verification
        suspended_pos = content.index("## Suspended")
        verification_pos = content.index("## Verification")
        self.assertLess(suspended_pos, verification_pos)

    def test_appends_suspended_section_with_backlog_target(self):
        self.task_file.write_text(
            "---\nkind: task\nname: 0042-test-task\nstatus: backlog\n---\n\n"
            "# Test Task\n\n## Requirements\n\nDo stuff.\n\n## Verification\n\n- [ ] done\n"
        )
        stdout, stderr, rc = _run_hook(self._env("backlog"), self.tmpdir, stdin_text="\nn\n")
        self.assertEqual(rc, 0, f"Hook failed: {stderr}")
        content = self.task_file.read_text()
        self.assertIn("**Target:** backlog", content)

    def test_multiple_suspensions_append_with_separator(self):
        # Pre-populate with an existing ## Suspended section
        self.task_file.write_text(
            "---\nkind: task\nname: 0042-test-task\nstatus: ready\n---\n\n"
            "# Test Task\n\n## Requirements\n\nDo stuff.\n\n"
            "## Suspended\n\n"
            "**Date:** 2026-03-15\n"
            "**Target:** ready\n"
            "**Reason:** first time\n"
            "**Branch:** —\n\n"
            "## Verification\n\n- [ ] done\n"
        )
        stdout, stderr, rc = _run_hook(self._env("backlog"), self.tmpdir, stdin_text="\nn\n")
        self.assertEqual(rc, 0, f"Hook failed: {stderr}")
        content = self.task_file.read_text()
        # Should have two entries: original and new
        self.assertIn("**Target:** ready", content)
        self.assertIn("**Target:** backlog", content)
        # Should have a --- separator between entries
        suspended_idx = content.index("## Suspended")
        rest = content[suspended_idx:]
        self.assertIn("---", rest)

    def test_no_branch_when_no_uncommitted_changes(self):
        self.task_file.write_text(
            "---\nkind: task\nname: 0042-test-task\nstatus: ready\n---\n\n"
            "# Test Task\n\n## Verification\n\n- [ ] done\n"
        )
        stdout, stderr, rc = _run_hook(self._env(), self.tmpdir, stdin_text="\nn\n")
        self.assertEqual(rc, 0, f"Hook failed: {stderr}")
        content = self.task_file.read_text()
        self.assertIn("**Branch:** —", content)

    def test_exits_silently_for_wrong_old_status(self):
        """Hook should exit 0 (no-op) if old status is not in-progress."""
        self.task_file.write_text(
            "---\nkind: task\nname: 0042-test-task\nstatus: ready\n---\n\n# Test\n"
        )
        env = self._env()
        env["OS_OLD_STATUS"] = "review"
        _, _, rc = _run_hook(env, self.tmpdir)
        self.assertEqual(rc, 0)
        # Task file should be unchanged
        content = self.task_file.read_text()
        self.assertNotIn("## Suspended", content)

    def test_confirmation_message(self):
        self.task_file.write_text(
            "---\nkind: task\nname: 0042-test-task\nstatus: ready\n---\n\n"
            "# Test Task\n\n## Verification\n\n- [ ] done\n"
        )
        stdout, stderr, rc = _run_hook(self._env(), self.tmpdir, stdin_text="\nn\n")
        self.assertEqual(rc, 0)
        self.assertIn("suspended → ready", stdout)


class TestSuspendTransitionTable(unittest.TestCase):
    """Test that the transition table allows suspend transitions."""

    def test_in_progress_to_ready_is_valid(self):
        from openstation.core import VALID_TRANSITIONS
        self.assertIn(("in-progress", "ready"), VALID_TRANSITIONS)

    def test_in_progress_to_backlog_is_valid(self):
        from openstation.core import VALID_TRANSITIONS
        self.assertIn(("in-progress", "backlog"), VALID_TRANSITIONS)


if __name__ == "__main__":
    unittest.main()
