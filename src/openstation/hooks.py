"""Task lifecycle hooks — run commands on status transitions.

Hooks support two phases:
  - ``"pre"``  (default) — runs before status is written; failure aborts.
  - ``"post"`` — runs after status is written; failure is a warning only.
"""

import json
import os
import subprocess
from pathlib import Path
from typing import Optional

from openstation import core

DEFAULT_TIMEOUT = 30
_SIGKILL_GRACE = 5
VALID_PHASES = ("pre", "post")


def _settings_path(root: Path) -> Path:
    """Return the settings file path for the vault."""
    from openstation.core import vault_path
    return vault_path(root, "settings.json")


def load_settings(root: Path) -> dict:
    """Read the full settings.json for the vault.

    Returns an empty dict if the file is missing or invalid.
    """
    path = _settings_path(root)
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return {}

    try:
        data = json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return {}

    if not isinstance(data, dict):
        return {}

    return data


def load_hooks(root: Path) -> list[dict]:
    """Read StatusTransition hooks from settings.json.

    Returns an empty list if the file is missing, has no
    'hooks' key, or has no 'StatusTransition' key.
    """
    data = load_settings(root)

    hooks = data.get("hooks", {})
    if not isinstance(hooks, dict):
        return []

    entries = hooks.get("StatusTransition", [])
    if not isinstance(entries, list):
        return []

    return entries


def _normalize_matcher(matcher: str) -> str:
    """Normalize ASCII '->' to Unicode '→'."""
    return matcher.replace("->", "\u2192")


def match_hooks(
    hooks: list[dict], old: str, new: str, *, phase: str = "pre"
) -> list[dict]:
    """Filter hooks whose matcher matches the (old, new) pair and phase.

    *phase* must be ``"pre"`` or ``"post"``.  Hooks without an explicit
    ``phase`` field default to ``"pre"``.

    Returns matching hooks in declaration order.
    """
    matched = []
    for hook in hooks:
        hook_phase = hook.get("phase", "pre")
        if hook_phase not in VALID_PHASES:
            hook_phase = "pre"
        if hook_phase != phase:
            continue
        matcher = hook.get("matcher", "")
        matcher = _normalize_matcher(matcher)
        if "\u2192" not in matcher:
            continue
        left, right = matcher.split("\u2192", 1)
        left = left.strip()
        right = right.strip()
        if (left == "*" or left == old) and (right == "*" or right == new):
            matched.append(hook)
    return matched


def _run_hook(hook: dict, env: dict) -> tuple[bool, str]:
    """Execute a single hook command.

    Returns (success, error_message). On success error_message is empty.
    """
    command = hook.get("command", "")
    if not command:
        return True, ""

    timeout = hook.get("timeout", DEFAULT_TIMEOUT)
    if not isinstance(timeout, (int, float)) or timeout <= 0:
        timeout = DEFAULT_TIMEOUT

    try:
        proc = subprocess.Popen(
            command,
            shell=True,
            env=env,
        )
    except OSError as exc:
        return False, f"hook failed to start: {command} ({exc})"

    try:
        proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        # SIGTERM first
        try:
            proc.terminate()
        except OSError:
            pass
        try:
            proc.wait(timeout=_SIGKILL_GRACE)
        except subprocess.TimeoutExpired:
            try:
                proc.kill()
            except OSError:
                pass
            proc.wait()
        return False, f"hook timed out after {int(timeout)}s: {command}"

    if proc.returncode != 0:
        return False, f"hook failed: {command} (exit {proc.returncode})"

    return True, ""


def _build_hook_env(
    root: Path, task_name: str, old: str, new: str, task_file: Path,
) -> dict:
    """Build the OS_ environment dict for hook execution."""
    env = os.environ.copy()
    env["OS_TASK_NAME"] = task_name
    env["OS_OLD_STATUS"] = old
    env["OS_NEW_STATUS"] = new
    env["OS_TASK_FILE"] = str(task_file.resolve())
    env["OS_VAULT_ROOT"] = str(root.resolve())
    return env


def run_matched(
    root: Path,
    task_name: str,
    old: str,
    new: str,
    task_file: Path,
    *,
    phase: str = "pre",
) -> Optional[int]:
    """Load, match, and execute hooks for a transition.

    *phase* selects which hooks to run (``"pre"`` or ``"post"``).

    **Pre-hooks** — returns ``None`` on success, ``EXIT_HOOK_FAILED``
    on failure.  First failure aborts remaining hooks.

    **Post-hooks** — always returns ``None``.  Failures are reported
    as warnings (via ``core.err``) but do **not** roll back the
    transition.
    """
    all_hooks = load_hooks(root)
    matched = match_hooks(all_hooks, old, new, phase=phase)

    if not matched:
        return None

    env = _build_hook_env(root, task_name, old, new, task_file)

    for hook in matched:
        ok, err_msg = _run_hook(hook, env)
        if not ok:
            if phase == "pre":
                core.err(err_msg)
                return core.EXIT_HOOK_FAILED
            else:
                # Post-hook failure is a warning only
                core.err(f"warning: {err_msg}")

    return None
