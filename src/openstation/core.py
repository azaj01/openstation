"""Shared foundations: vault discovery, frontmatter parsing, output helpers, constants."""

import os
import re
import subprocess
import sys
import time
from pathlib import Path

from openstation import __version__ as VERSION

# --- Exit codes ---------------------------------------------------------------

EXIT_OK = 0
EXIT_USAGE = 1
EXIT_NO_PROJECT = 2
EXIT_NOT_FOUND = 3
EXIT_AMBIGUOUS = 4
EXIT_TASK_NOT_READY = 5
EXIT_INVALID_TRANSITION = 6
EXIT_NO_CLAUDE = 7
EXIT_AGENT_ERROR = 8
EXIT_SOURCE_GUARD = 9

# --- Lifecycle constants ------------------------------------------------------

VALID_TRANSITIONS = {
    ("backlog", "ready"),
    ("ready", "in-progress"),
    ("in-progress", "review"),
    ("review", "done"),
    ("review", "failed"),
    ("failed", "in-progress"),
}

VALID_STATUSES = {"backlog", "ready", "in-progress", "review", "done", "failed"}

_STATUS_RANK = {"backlog": 0, "ready": 1, "in-progress": 2, "review": 3, "done": 4, "failed": 3}
_MIN_PARENT_STATUS = {"ready": "ready", "in-progress": "in-progress", "review": "in-progress",
                       "done": "in-progress", "failed": "in-progress"}

# --- Module-level state -------------------------------------------------------

_quiet = False
_run_start = None


def set_quiet(value):
    """Set the quiet flag (suppresses progress output)."""
    global _quiet
    _quiet = value


def set_run_start(value):
    """Set the run start timestamp (enables elapsed timestamps)."""
    global _run_start
    _run_start = value


# --- Error output -------------------------------------------------------------

def err(msg):
    print(f"error: {msg}", file=sys.stderr)


# --- Vault discovery ----------------------------------------------------------

def _check_dir(d):
    """Check a single directory for Open Station markers.

    Returns (root, prefix) or (None, None).
    """
    if (d / "agents").is_dir() and (d / "install.sh").is_file():
        return d, ""
    if (d / ".openstation").is_dir():
        return d, ".openstation"
    return None, None


def _git_main_worktree_root(start):
    """Resolve the main worktree root via git, or return None."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--git-common-dir"],
            cwd=str(start),
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            return None
        common_dir = Path(result.stdout.strip())
        if not common_dir.is_absolute():
            common_dir = (start / common_dir).resolve()
        # common_dir is the .git dir of the main worktree
        return common_dir.parent
    except (FileNotFoundError, OSError):
        return None


def find_root(start=None):
    """Walk up from start dir to find an Open Station project root.

    Returns (root_path, prefix) where prefix is ".openstation" for
    installed projects or "" for the source repo.

    Falls back to checking the main git worktree root when the local
    walk-up finds nothing and CWD is inside a git worktree.
    """
    d = Path(start or os.getcwd()).resolve()
    while True:
        root, prefix = _check_dir(d)
        if root is not None:
            return root, prefix
        parent = d.parent
        if parent == d:
            break
        d = parent

    # Fallback: try main worktree root
    start_path = Path(start or os.getcwd()).resolve()
    main_root = _git_main_worktree_root(start_path)
    if main_root is not None:
        root, prefix = _check_dir(main_root)
        if root is not None:
            return root, prefix

    return None, None


def tasks_dir_path(root, prefix):
    """Return the Path to artifacts/tasks/ for the given root and prefix."""
    if prefix:
        return Path(root) / prefix / "artifacts" / "tasks"
    return Path(root) / "artifacts" / "tasks"


# --- Frontmatter parsing -----------------------------------------------------

def parse_frontmatter(text):
    """Parse YAML frontmatter from text using simple str.partition."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    fields = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        key, sep, value = line.partition(":")
        if sep:
            fields[key.strip()] = value.strip()
    return fields


def parse_multiline_value(text, key):
    """Parse a YAML folded/literal block value (>-, >, |, |-) from frontmatter."""
    lines = text.splitlines()
    in_value = False
    parts = []
    for line in lines:
        if line.strip() == "---" and in_value:
            break
        if not in_value:
            if line.startswith(f"{key}:"):
                val = line.partition(":")[2].strip()
                if val in (">-", ">", "|", "|-"):
                    in_value = True
                    continue
                return val
        else:
            if line.startswith("  "):
                parts.append(line.strip())
            else:
                break
    return " ".join(parts)


def strip_wikilink(value):
    """Strip Obsidian wikilink syntax and quotes: '"[[name]]"' → 'name'."""
    value = value.strip().strip("\"'")
    if value.startswith("[[") and value.endswith("]]"):
        value = value[2:-2]
    return value


def parse_frontmatter_list(text, key):
    """Parse a YAML list field from frontmatter.

    Handles both plain values and Obsidian wikilinks (``[[name]]``).
    Returns a list of strings for the given key, or [] if not found.
    """
    items = []
    in_list = False
    for line in text.splitlines():
        if line.strip() == "---" and in_list:
            break
        if line.startswith(f"{key}:"):
            in_list = True
            continue
        if in_list:
            if re.match(r"^\s*-\s+", line):
                value = re.sub(r"^\s*-\s+", "", line).strip()
                items.append(strip_wikilink(value))
            else:
                break
    return items


def extract_body(text):
    """Extract the markdown body after YAML frontmatter."""
    lines = text.splitlines(keepends=True)
    fm_count = 0
    body_start = 0
    for i, line in enumerate(lines):
        if line.strip() == "---":
            fm_count += 1
            if fm_count == 2:
                body_start = i + 1
                break
    return "".join(lines[body_start:]).strip()


def parse_frontmatter_for_json(text):
    """Parse frontmatter into a dict suitable for JSON serialization.

    Handles simple key-value fields and list fields (subtasks, artifacts).
    """
    fm = parse_frontmatter(text)
    for list_key in ("subtasks", "artifacts"):
        items = parse_frontmatter_list(text, list_key)
        if items:
            fm[list_key] = items
        elif list_key in fm:
            del fm[list_key]
    return fm


# --- Text utilities -----------------------------------------------------------

def slugify(description, max_words=5):
    """Convert a description string to a kebab-case slug."""
    slug = re.sub(r"[^a-z0-9]+", "-", description.lower()).strip("-")
    slug = re.sub(r"-+", "-", slug)
    parts = slug.split("-")[:max_words]
    return "-".join(parts) or "untitled"


def title_from_description(description, max_len=80):
    """Derive an H1 title from a description string."""
    title = description.strip().title()
    if len(title) <= max_len:
        return title
    truncated = title[:max_len]
    last_space = truncated.rfind(" ")
    if last_space > 0:
        return truncated[:last_space]
    return truncated


def shlex_join(cmd):
    """Join a command list into a shell-safe string."""
    import shlex
    return " ".join(shlex.quote(arg) for arg in cmd)


# --- Output helpers (all print to stderr) ------------------------------------

def info(msg):
    """Print an info message to stderr."""
    if not _quiet:
        print(f"{_ts()}info: {msg}", file=sys.stderr)


def _use_color():
    """Return True if ANSI color output should be used."""
    return sys.stderr.isatty() and not os.environ.get("NO_COLOR")


def _green(s):  return f"\033[32m{s}\033[0m" if _use_color() else str(s)
def _red(s):    return f"\033[31m{s}\033[0m" if _use_color() else str(s)
def _bold(s):   return f"\033[1m{s}\033[0m" if _use_color() else str(s)
def _dim(s):    return f"\033[2m{s}\033[0m" if _use_color() else str(s)


def _ts():
    """Return a dim wall-clock prefix like '[14:32] ', or '' if not in a run."""
    if _run_start is None:
        return ""
    now = time.localtime()
    return _dim(f"[{now.tm_hour}:{now.tm_min:02d}] ")


def header(text):
    """Print a section separator: ── text ─────────"""
    if _quiet:
        return
    width = 48
    line = f"── {text} " + "─" * max(0, width - len(text) - 4)
    print(f"{_ts()}{_bold(line)}", file=sys.stderr)


def step(n, total, name):
    """Print a step indicator: [1/3] task-name"""
    if _quiet:
        return
    print(f"\n{_ts()}{_bold(f'[{n}/{total}]')} {name}", file=sys.stderr)


def detail(label, value):
    """Print an indented detail line: label: value"""
    if _quiet:
        return
    print(f"{_ts()}      {_dim(label + ':')} {value}", file=sys.stderr)


def success(msg):
    """Print a success line: ✓ msg (green)"""
    if _quiet:
        return
    print(f"{_ts()}      {_green('✓')} {msg}", file=sys.stderr)


def failure(msg):
    """Print a failure line: ✗ msg (red, always prints even in quiet)"""
    print(f"{_ts()}      {_red('✗')} {msg}", file=sys.stderr)


def remaining_line(msg):
    """Print a remaining-items line: · msg"""
    if _quiet:
        return
    print(f"{_ts()}      · {msg}", file=sys.stderr)


def hint(msg):
    """Print a dim hint line."""
    if _quiet:
        return
    print(f"{_ts()}  {_dim(msg)}", file=sys.stderr)


def format_duration(seconds):
    """Format seconds as '45s' or '2m 05s'."""
    if seconds < 60:
        return f"{seconds:.0f}s"
    m, s = divmod(int(seconds), 60)
    return f"{m}m {s:02d}s"


def summary_block(completed, failed, pending, resume_cmd=None, next_task=None):
    """Print a run summary block with counts and resume hint."""
    if not _quiet:
        print(file=sys.stderr)
    header("Summary")
    if completed:
        success(f"{completed} completed")
    if failed:
        failure(f"{failed} failed")
    if pending:
        remaining_line(f"{pending} remaining")
    if next_task and not _quiet:
        print(f"\n  Next: {next_task}", file=sys.stderr)
    if resume_cmd and pending > 0 and not _quiet:
        print(f"\n  To continue:", file=sys.stderr)
        print(f"    {resume_cmd}", file=sys.stderr)
