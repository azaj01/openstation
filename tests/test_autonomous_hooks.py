"""Tests for autonomous chaining hooks and os-dispatch."""

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BIN_DIR = PROJECT_ROOT / "bin"
HOOKS_DIR = BIN_DIR / "hooks"


def _run_script(script_path, env, cwd=None):
    """Run a bash script and return (stdout, stderr, returncode)."""
    result = subprocess.run(
        ["bash", str(script_path)],
        capture_output=True,
        text=True,
        cwd=str(cwd) if cwd else None,
        env=env,
    )
    return result.stdout, result.stderr, result.returncode


def _make_settings(tmpdir, autonomous_enabled=False):
    """Create .openstation/settings.json in tmpdir."""
    os_dir = tmpdir / ".openstation"
    os_dir.mkdir(parents=True, exist_ok=True)
    settings = {
        "hooks": {"StatusTransition": []},
        "autonomous": {"enabled": autonomous_enabled},
    }
    (os_dir / "settings.json").write_text(json.dumps(settings))


def _make_task_file(tmpdir, assignee="developer"):
    """Create a minimal task file and return its path."""
    task_file = tmpdir / "task.md"
    assignee_line = f"assignee: {assignee}" if assignee else ""
    task_file.write_text(
        f"---\nkind: task\nname: 0042-test-task\nstatus: ready\n{assignee_line}\n---\n\n# Test\n"
    )
    return task_file


def _base_env(tmpdir, task_file=None):
    """Build base env dict for hook scripts."""
    return {
        "OS_TASK_NAME": "0042-test-task",
        "OS_TASK_FILE": str(task_file or tmpdir / "task.md"),
        "OS_VAULT_ROOT": str(tmpdir),
        "PATH": os.environ.get("PATH", ""),
        "HOME": os.environ.get("HOME", ""),
    }


# ── os-dispatch ──────────────────────────────────────────────


class TestOsDispatch(unittest.TestCase):
    """Tests for bin/os-dispatch."""

    script = BIN_DIR / "os-dispatch"

    def test_missing_args_exits_1(self):
        """os-dispatch with no args should exit 1."""
        _, stderr, rc = _run_script(self.script, env=os.environ.copy())
        self.assertEqual(rc, 1)
        self.assertIn("usage:", stderr)

    def test_one_arg_exits_1(self):
        """os-dispatch with only window name should exit 1."""
        result = subprocess.run(
            ["bash", str(self.script), "test-window"],
            capture_output=True, text=True, env=os.environ.copy(),
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("usage:", result.stderr)

    def test_nohup_fallback_when_no_tmux_binary(self):
        """When tmux binary is absent, os-dispatch falls back to nohup."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            _make_settings(tmpdir)
            # Build a PATH that excludes tmux by only including dirs
            # with basic utilities but not tmux
            stub_bin = Path(tmpdir) / "stub-bin"
            stub_bin.mkdir()
            # Symlink essential commands needed by the script
            for cmd in ("env", "nohup", "mkdir", "bash"):
                src = subprocess.run(
                    ["which", cmd], capture_output=True, text=True
                ).stdout.strip()
                if src:
                    (stub_bin / cmd).symlink_to(src)
            env = {
                "PATH": str(stub_bin),
                "HOME": os.environ.get("HOME", ""),
                "OS_VAULT_ROOT": str(tmpdir),
            }
            result = subprocess.run(
                ["bash", str(self.script), "test-win", "true"],
                capture_output=True, text=True, env=env,
            )
            self.assertEqual(result.returncode, 0)
            self.assertIn("tmux not found", result.stdout)

    def test_nohup_message_only_when_no_tmux_binary(self):
        """nohup fallback message should not appear when tmux exists but server is down."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            _make_settings(tmpdir)
            env = {
                "PATH": os.environ.get("PATH", ""),
                "HOME": os.environ.get("HOME", ""),
                "OS_VAULT_ROOT": str(tmpdir),
            }
            result = subprocess.run(
                ["bash", str(self.script), "test-win", "true"],
                capture_output=True, text=True, env=env,
            )
            # tmux is on PATH, so nohup message must not appear
            self.assertNotIn("tmux not found", result.stdout)
            self.assertNotIn("nohup", result.stdout)

    def test_no_attach_flag_accepted(self):
        """os-dispatch accepts --no-attach without error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            _make_settings(tmpdir)
            env = {
                "PATH": os.environ.get("PATH", ""),
                "HOME": os.environ.get("HOME", ""),
                "OS_VAULT_ROOT": str(tmpdir),
            }
            result = subprocess.run(
                ["bash", str(self.script), "--no-attach", "test-win", "true"],
                capture_output=True, text=True, env=env,
            )
            # Should not fail on args parsing
            self.assertNotIn("usage:", result.stderr)

    def test_no_attach_flag_before_window_name(self):
        """--no-attach must come before window name; args after it parse correctly."""
        result = subprocess.run(
            ["bash", str(self.script), "--no-attach"],
            capture_output=True, text=True, env=os.environ.copy(),
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("usage:", result.stderr)


# ── auto-start ───────────────────────────────────────────────


class TestAutoStart(unittest.TestCase):
    """Tests for bin/hooks/auto-start."""

    script = HOOKS_DIR / "auto-start"

    def test_missing_env_vars_exits_1(self):
        """auto-start without required env vars should exit 1."""
        env = {"PATH": os.environ.get("PATH", ""), "HOME": os.environ.get("HOME", "")}
        _, stderr, rc = _run_script(self.script, env=env)
        self.assertEqual(rc, 1)
        self.assertIn("missing required env var", stderr)

    def test_noop_when_autonomous_disabled(self):
        """auto-start should exit 0 (no-op) when autonomous.enabled is false."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            _make_settings(tmpdir, autonomous_enabled=False)
            task_file = _make_task_file(tmpdir)
            env = _base_env(tmpdir, task_file)
            _, _, rc = _run_script(self.script, env=env)
            self.assertEqual(rc, 0)

    def test_noop_when_depth_exceeds_max(self):
        """auto-start should exit 0 when OS_HOOK_DEPTH >= max."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            _make_settings(tmpdir, autonomous_enabled=True)
            task_file = _make_task_file(tmpdir)
            env = _base_env(tmpdir, task_file)
            env["OS_HOOK_DEPTH"] = "10"
            env["OS_MAX_HOOK_DEPTH"] = "5"
            _, stderr, rc = _run_script(self.script, env=env)
            self.assertEqual(rc, 0)
            self.assertIn("hook depth", stderr)

    def test_noop_when_no_assignee(self):
        """auto-start should exit 0 when task has no assignee."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            _make_settings(tmpdir, autonomous_enabled=True)
            task_file = _make_task_file(tmpdir, assignee="")
            env = _base_env(tmpdir, task_file)
            _, stderr, rc = _run_script(self.script, env=env)
            self.assertEqual(rc, 0)
            self.assertIn("no assignee", stderr)

    def test_noop_at_exact_max_depth(self):
        """auto-start should stop at exactly max depth."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            _make_settings(tmpdir, autonomous_enabled=True)
            task_file = _make_task_file(tmpdir)
            env = _base_env(tmpdir, task_file)
            env["OS_HOOK_DEPTH"] = "5"
            env["OS_MAX_HOOK_DEPTH"] = "5"
            _, stderr, rc = _run_script(self.script, env=env)
            self.assertEqual(rc, 0)
            self.assertIn("hook depth", stderr)

    def test_passes_through_when_depth_below_max(self):
        """auto-start at depth < max should attempt dispatch (and fail on os-dispatch missing openstation, but not on guards)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            _make_settings(tmpdir, autonomous_enabled=True)
            task_file = _make_task_file(tmpdir, assignee="developer")
            env = _base_env(tmpdir, task_file)
            env["OS_HOOK_DEPTH"] = "1"
            env["OS_MAX_HOOK_DEPTH"] = "5"
            # Will fail at os-dispatch (not on PATH in test env) but
            # proves it got past all guards
            _, stderr, rc = _run_script(self.script, env=env)
            # Non-zero because os-dispatch or openstation won't be found,
            # but it should NOT contain our guard messages
            self.assertNotIn("hook depth", stderr)
            self.assertNotIn("no assignee", stderr)

    def test_passes_no_attach_to_os_dispatch(self):
        """auto-start must pass --no-attach to os-dispatch so tier 2 doesn't block the hook."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            _make_settings(tmpdir, autonomous_enabled=True)
            task_file = _make_task_file(tmpdir, assignee="developer")
            # Create a stub os-dispatch that logs its args
            bin_dir = tmpdir / "bin"
            bin_dir.mkdir()
            stub = bin_dir / "os-dispatch"
            stub.write_text(
                '#!/usr/bin/env bash\necho "ARGS: $*"\nexit 0\n'
            )
            stub.chmod(0o755)
            env = _base_env(tmpdir, task_file)
            env["OS_HOOK_DEPTH"] = "0"
            env["OS_MAX_HOOK_DEPTH"] = "5"
            stdout, _, rc = _run_script(self.script, env=env)
            self.assertEqual(rc, 0)
            self.assertIn("--no-attach", stdout)


# ── auto-verify ──────────────────────────────────────────────


class TestAutoVerify(unittest.TestCase):
    """Tests for bin/hooks/auto-verify."""

    script = HOOKS_DIR / "auto-verify"

    def test_missing_env_vars_exits_1(self):
        env = {"PATH": os.environ.get("PATH", ""), "HOME": os.environ.get("HOME", "")}
        _, stderr, rc = _run_script(self.script, env=env)
        self.assertEqual(rc, 1)
        self.assertIn("missing required env var", stderr)

    def test_noop_when_autonomous_disabled(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            _make_settings(tmpdir, autonomous_enabled=False)
            task_file = _make_task_file(tmpdir)
            env = _base_env(tmpdir, task_file)
            _, _, rc = _run_script(self.script, env=env)
            self.assertEqual(rc, 0)

    def test_noop_when_depth_exceeds_max(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            _make_settings(tmpdir, autonomous_enabled=True)
            task_file = _make_task_file(tmpdir)
            env = _base_env(tmpdir, task_file)
            env["OS_HOOK_DEPTH"] = "10"
            env["OS_MAX_HOOK_DEPTH"] = "5"
            _, stderr, rc = _run_script(self.script, env=env)
            self.assertEqual(rc, 0)
            self.assertIn("hook depth", stderr)


# ── auto-accept ──────────────────────────────────────────────


class TestAutoAccept(unittest.TestCase):
    """Tests for bin/hooks/auto-accept."""

    script = HOOKS_DIR / "auto-accept"

    def test_missing_env_vars_exits_1(self):
        env = {"PATH": os.environ.get("PATH", ""), "HOME": os.environ.get("HOME", "")}
        _, stderr, rc = _run_script(self.script, env=env)
        self.assertEqual(rc, 1)
        self.assertIn("missing required env var", stderr)

    def test_noop_when_autonomous_disabled(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            _make_settings(tmpdir, autonomous_enabled=False)
            env = {
                "OS_TASK_NAME": "0042-test-task",
                "OS_VAULT_ROOT": str(tmpdir),
                "PATH": os.environ.get("PATH", ""),
                "HOME": os.environ.get("HOME", ""),
            }
            _, _, rc = _run_script(self.script, env=env)
            self.assertEqual(rc, 0)

    def test_noop_when_depth_exceeds_max(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            _make_settings(tmpdir, autonomous_enabled=True)
            env = {
                "OS_TASK_NAME": "0042-test-task",
                "OS_VAULT_ROOT": str(tmpdir),
                "PATH": os.environ.get("PATH", ""),
                "HOME": os.environ.get("HOME", ""),
                "OS_HOOK_DEPTH": "10",
                "OS_MAX_HOOK_DEPTH": "5",
            }
            _, stderr, rc = _run_script(self.script, env=env)
            self.assertEqual(rc, 0)
            self.assertIn("hook depth", stderr)


# ── settings.json ────────────────────────────────────────────


class TestSettingsJson(unittest.TestCase):
    """Verify settings.json has the correct autonomous config."""

    def setUp(self):
        settings_path = PROJECT_ROOT / ".openstation" / "settings.json"
        with open(settings_path) as f:
            self.settings = json.load(f)

    def test_autonomous_section_exists(self):
        self.assertIn("autonomous", self.settings)
        self.assertFalse(self.settings["autonomous"]["enabled"])

    def test_auto_start_hook_registered(self):
        hooks = self.settings["hooks"]["StatusTransition"]
        matchers = [(h["matcher"], h["command"]) for h in hooks]
        self.assertIn(("*→ready", "bin/hooks/auto-start"), matchers)

    def test_auto_verify_hook_registered(self):
        hooks = self.settings["hooks"]["StatusTransition"]
        matchers = [(h["matcher"], h["command"]) for h in hooks]
        self.assertIn(("*→review", "bin/hooks/auto-verify"), matchers)

    def test_auto_accept_hook_registered(self):
        hooks = self.settings["hooks"]["StatusTransition"]
        matchers = [(h["matcher"], h["command"]) for h in hooks]
        self.assertIn(("*→verified", "bin/hooks/auto-accept"), matchers)

    def test_autonomous_hooks_are_first(self):
        """Autonomous hooks should appear before existing hooks."""
        hooks = self.settings["hooks"]["StatusTransition"]
        commands = [h["command"] for h in hooks]
        auto_start_idx = commands.index("bin/hooks/auto-start")
        auto_commit_idx = commands.index("bin/hooks/auto-commit")
        self.assertLess(auto_start_idx, auto_commit_idx)

    def test_existing_hooks_preserved(self):
        hooks = self.settings["hooks"]["StatusTransition"]
        matchers = [(h["matcher"], h["command"]) for h in hooks]
        self.assertIn(("*→done", "bin/hooks/auto-commit"), matchers)
        self.assertIn(("in-progress→ready", "bin/hooks/suspend"), matchers)
        self.assertIn(("in-progress→backlog", "bin/hooks/suspend"), matchers)


if __name__ == "__main__":
    unittest.main()
