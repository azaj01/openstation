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


# ---------------------------------------------------------------------------
# CLI subcommands: hooks list / show / run
# ---------------------------------------------------------------------------

def _format_hook_row(idx: int, hook: dict) -> tuple[str, str, str, str, str]:
    """Return (index, matcher, command, phase, timeout) strings for a hook."""
    return (
        str(idx),
        hook.get("matcher", ""),
        hook.get("command", ""),
        hook.get("phase", "pre"),
        str(hook.get("timeout", DEFAULT_TIMEOUT)),
    )


def cmd_hooks_list(_args, root) -> int:
    """Print all configured StatusTransition hooks."""
    entries = load_hooks(root)
    if not entries:
        print("No hooks configured in settings.json")
        return core.EXIT_OK

    # Table header
    hdr = f"{'#':<4} {'Matcher':<28} {'Phase':<6} {'Timeout':<8} {'Command'}"
    print(hdr)
    print("─" * len(hdr))
    for i, hook in enumerate(entries):
        idx, matcher, command, phase, timeout = _format_hook_row(i, hook)
        print(f"{idx:<4} {matcher:<28} {phase:<6} {timeout + 's':<8} {command}")
    return core.EXIT_OK


def cmd_hooks_show(args, root) -> int:
    """Display a single hook entry with full details."""
    entries = load_hooks(root)
    if not entries:
        core.err("no hooks configured in settings.json")
        return core.EXIT_NOT_FOUND

    query = args.hook_query

    # Try numeric index first
    try:
        idx = int(query)
        if 0 <= idx < len(entries):
            _print_hook_detail(idx, entries[idx])
            return core.EXIT_OK
        core.err(f"hook index {idx} out of range (0–{len(entries) - 1})")
        return core.EXIT_NOT_FOUND
    except ValueError:
        pass

    # Try matcher match
    found = [(i, h) for i, h in enumerate(entries)
             if _normalize_matcher(h.get("matcher", "")) == _normalize_matcher(query)]
    if not found:
        core.err(f"no hook matching '{query}'")
        return core.EXIT_NOT_FOUND
    if len(found) > 1:
        core.err(f"ambiguous matcher '{query}' — matches indices: "
                 + ", ".join(str(i) for i, _ in found))
        return core.EXIT_AMBIGUOUS
    _print_hook_detail(found[0][0], found[0][1])
    return core.EXIT_OK


def _print_hook_detail(idx: int, hook: dict) -> None:
    """Print full details for a single hook."""
    print(f"Index:   {idx}")
    print(f"Matcher: {hook.get('matcher', '')}")
    print(f"Command: {hook.get('command', '')}")
    print(f"Phase:   {hook.get('phase', 'pre')}")
    print(f"Timeout: {hook.get('timeout', DEFAULT_TIMEOUT)}s")


def cmd_hooks_run(args, root) -> int:
    """Manually trigger matching hooks for a simulated transition."""
    from openstation.tasks import resolve_task

    task_query = args.task
    old_status = args.old_status
    new_status = args.new_status
    phase_filter = getattr(args, "phase", "all")
    dry_run = getattr(args, "dry_run", False)

    # Validate statuses
    if old_status not in core.VALID_STATUSES:
        core.err(f"invalid old status: {old_status}")
        return core.EXIT_USAGE
    if new_status not in core.VALID_STATUSES:
        core.err(f"invalid new status: {new_status}")
        return core.EXIT_USAGE

    # Resolve task
    name, err_msg, exit_code = resolve_task(root, task_query)
    if name is None:
        core.err(err_msg)
        return exit_code

    task_file = core.tasks_dir_path(root) / f"{name}.md"

    # Load and match hooks
    all_hooks = load_hooks(root)
    phases = ["pre", "post"] if phase_filter == "all" else [phase_filter]
    matched = []
    for ph in phases:
        for hook in match_hooks(all_hooks, old_status, new_status, phase=ph):
            matched.append((ph, hook))

    if not matched:
        print(f"No hooks match {old_status}→{new_status}")
        return core.EXIT_OK

    if dry_run:
        print(f"Dry run: {old_status}→{new_status} for task {name}")
        print(f"{'#':<4} {'Phase':<6} {'Matcher':<28} {'Command'}")
        print("─" * 60)
        for ph, hook in matched:
            print(f"{all_hooks.index(hook):<4} {ph:<6} "
                  f"{hook.get('matcher', ''):<28} {hook.get('command', '')}")
        return core.EXIT_OK

    # Execute hooks
    env = _build_hook_env(root, name, old_status, new_status, task_file)
    for ph, hook in matched:
        cmd = hook.get("command", "")
        print(f"Running [{ph}] {cmd}")
        ok, err_msg = _run_hook(hook, env)
        if not ok:
            core.err(err_msg)
            if ph == "pre":
                return core.EXIT_HOOK_FAILED
            # post-hook failure: warn and continue

    return core.EXIT_OK
