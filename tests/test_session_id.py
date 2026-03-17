"""Tests for session ID capture in openstation run."""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SRC_DIR = str(Path(__file__).resolve().parent.parent / "src")
sys.path.insert(0, SRC_DIR)

from openstation.run import extract_session_id


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
    root = Path(tmpdir)
    (root / "agents").mkdir(parents=True, exist_ok=True)
    (root / "install.sh").write_text("#!/bin/bash\n")
    (root / "artifacts" / "tasks").mkdir(parents=True, exist_ok=True)
    return root


def make_agent_spec(base, name):
    agents_dir = base / "agents"
    agents_dir.mkdir(parents=True, exist_ok=True)
    (agents_dir / f"{name}.md").write_text(
        f"---\nkind: agent\nname: {name}\n"
        f"description: Test agent\nmodel: claude-sonnet-4-6\n"
        f"allowed-tools:\n  - Read\n  - Glob\n  - Grep\n---\n\n# {name}\n"
    )


def make_task(base, name, status="ready", assignee="researcher", subtasks=None, parent=None):
    tasks_dir = base / "artifacts" / "tasks"
    tasks_dir.mkdir(parents=True, exist_ok=True)
    extra = ""
    if subtasks:
        extra = "subtasks:\n" + "".join(f"  - {s}\n" for s in subtasks)
    if parent:
        extra += f'parent: "[[{parent}]]"\n'
    (tasks_dir / f"{name}.md").write_text(
        f"---\nkind: task\nname: {name}\nstatus: {status}\n"
        f"assignee: {assignee}\nowner: manual\ncreated: 2026-01-01\n"
        f"{extra}---\n\n# {name}\n"
    )


# --- Unit tests for extract_session_id ---


class TestExtractSessionId(unittest.TestCase):

    def test_extracts_from_init_message(self):
        line = json.dumps({"type": "system", "subtype": "init", "session_id": "abc-123-def"})
        self.assertEqual(extract_session_id(line), "abc-123-def")

    def test_extracts_from_any_object_with_session_id(self):
        line = json.dumps({"session_id": "sess-456", "other": "data"})
        self.assertEqual(extract_session_id(line), "sess-456")

    def test_returns_none_for_no_session_id(self):
        line = json.dumps({"type": "assistant", "content": "hello"})
        self.assertIsNone(extract_session_id(line))

    def test_returns_none_for_invalid_json(self):
        self.assertIsNone(extract_session_id("not json"))

    def test_returns_none_for_empty_string(self):
        self.assertIsNone(extract_session_id(""))

    def test_returns_none_for_json_array(self):
        self.assertIsNone(extract_session_id("[1, 2, 3]"))


# --- Integration tests with mock claude ---


SESSION_UUID = "test-session-uuid-12345"


def _make_mock_claude(tmpdir, exit_code=0, session_id=SESSION_UUID):
    """Create a mock claude that outputs stream-json with a session_id."""
    mock_bin = Path(tmpdir) / "_mock_bin"
    mock_bin.mkdir(exist_ok=True)
    mock_log = Path(tmpdir) / "claude_args.log"

    # Build stream-json output lines
    init_line = json.dumps({"type": "system", "subtype": "init", "session_id": session_id})
    result_line = json.dumps({"type": "result", "result": "task completed"})
    output = f'{init_line}\\n{result_line}\\n'

    mock_claude = mock_bin / "claude"
    mock_claude.write_text(
        f'#!/bin/bash\n'
        f'echo "$@" > {mock_log}\n'
        f'printf \'{output}\'\n'
        f'exit {exit_code}\n'
    )
    mock_claude.chmod(0o755)
    return mock_bin, mock_log


class TestSessionIdCapture(unittest.TestCase):
    """Test that session ID is captured from claude stream-json output."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.root = make_source_vault(self.tmpdir)
        make_agent_spec(self.root, "researcher")

        self.mock_bin, self.mock_log = _make_mock_claude(self.tmpdir)
        self.env = os.environ.copy()
        self.env["PATH"] = f"{self.mock_bin}:{self.env.get('PATH', '')}"

    def _run(self, args):
        env = dict(self.env)
        existing = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = SRC_DIR + (os.pathsep + existing if existing else "")
        result = subprocess.run(
            [sys.executable, "-m", "openstation"] + args,
            capture_output=True,
            text=True,
            cwd=self.tmpdir,
            env=env,
        )
        return result.stdout, result.stderr, result.returncode

    def test_session_id_in_subtask_log(self):
        """Session ID appears in stderr when running subtask queue."""
        make_task(self.root, "0001-parent", status="ready", assignee="researcher",
                  subtasks=["0002-child"])
        make_task(self.root, "0002-child", status="ready", assignee="researcher")

        _, stderr, rc = self._run(["run", "--task", "0001-parent"])
        self.assertEqual(rc, 0, f"stderr: {stderr}")
        self.assertIn(SESSION_UUID, stderr)
        self.assertIn("session:", stderr)

    def test_session_id_in_jsonl_log(self):
        """Session ID is present in the JSONL log file."""
        make_task(self.root, "0001-parent", status="ready", assignee="researcher",
                  subtasks=["0002-child"])
        make_task(self.root, "0002-child", status="ready", assignee="researcher")

        self._run(["run", "--task", "0001-parent"])
        log_file = self.root / "artifacts" / "logs" / "0002-child.jsonl"
        self.assertTrue(log_file.exists(), "JSONL log file was not created")
        content = log_file.read_text()
        self.assertIn(SESSION_UUID, content)

    def test_session_id_in_single_task_log(self):
        """Session ID appears when running a single task (no subtasks)."""
        make_task(self.root, "0001-single", status="ready", assignee="researcher")

        _, stderr, rc = self._run(["run", "--task", "0001-single"])
        self.assertEqual(rc, 0, f"stderr: {stderr}")
        self.assertIn(SESSION_UUID, stderr)

    def test_session_id_in_single_task_jsonl(self):
        """JSONL log created for single task execution."""
        make_task(self.root, "0001-single", status="ready", assignee="researcher")

        self._run(["run", "--task", "0001-single"])
        log_file = self.root / "artifacts" / "logs" / "0001-single.jsonl"
        self.assertTrue(log_file.exists(), "JSONL log file was not created")
        content = log_file.read_text()
        self.assertIn(SESSION_UUID, content)


class TestResumeCommandOnFailure(unittest.TestCase):
    """Test that resume command is printed when claude fails."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.root = make_source_vault(self.tmpdir)
        make_agent_spec(self.root, "researcher")

        # Mock claude that exits with failure
        self.mock_bin, self.mock_log = _make_mock_claude(self.tmpdir, exit_code=1)
        self.env = os.environ.copy()
        self.env["PATH"] = f"{self.mock_bin}:{self.env.get('PATH', '')}"

    def _run(self, args):
        env = dict(self.env)
        existing = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = SRC_DIR + (os.pathsep + existing if existing else "")
        result = subprocess.run(
            [sys.executable, "-m", "openstation"] + args,
            capture_output=True,
            text=True,
            cwd=self.tmpdir,
            env=env,
        )
        return result.stdout, result.stderr, result.returncode

    def test_resume_command_on_subtask_failure(self):
        """Summary shows claude --resume <session-id> on failure."""
        make_task(self.root, "0001-parent", status="ready", assignee="researcher",
                  subtasks=["0002-child"])
        make_task(self.root, "0002-child", status="ready", assignee="researcher")

        _, stderr, rc = self._run(["run", "--task", "0001-parent"])
        self.assertNotEqual(rc, 0)
        self.assertIn(f"claude --resume {SESSION_UUID}", stderr)
        self.assertIn("Resume session:", stderr)

    def test_resume_command_on_single_task_failure(self):
        """Single task failure prints resume command."""
        make_task(self.root, "0001-single", status="ready", assignee="researcher")

        _, stderr, rc = self._run(["run", "--task", "0001-single"])
        self.assertNotEqual(rc, 0)
        self.assertIn(f"claude --resume {SESSION_UUID}", stderr)


class TestStreamJsonDryRun(unittest.TestCase):
    """Verify dry-run output shows stream-json format."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.root = make_source_vault(self.tmpdir)
        make_agent_spec(self.root, "researcher")

    def test_subtask_dry_run_shows_stream_json(self):
        """Subtask dry-run command uses stream-json format."""
        make_task(self.root, "0001-parent", status="ready", assignee="researcher",
                  subtasks=["0002-child"])
        make_task(self.root, "0002-child", status="ready", assignee="researcher")

        out, _, rc = run_cli(["run", "--task", "0001-parent", "--dry-run"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertIn("--output-format stream-json", out)

    def test_single_task_dry_run_shows_stream_json(self):
        """Single task dry-run command uses stream-json format."""
        make_task(self.root, "0001-single", status="ready", assignee="researcher")

        out, _, rc = run_cli(["run", "--task", "0001-single", "--dry-run"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertIn("--output-format stream-json", out)


if __name__ == "__main__":
    unittest.main()
