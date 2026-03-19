---
kind: spec
agent: architect
task: "[[0086-spec-module-split-for-src]]"
created: 2026-03-09
---

# Module Split for src/openstation/ Package

Design spec for extracting `bin/openstation` (~1968 lines, ~83
functions) into a `src/openstation/` Python package.

---

## Module Structure

Five modules under `src/openstation/`:

```
src/openstation/
├── __init__.py        # Package marker, exports __version__
├── core.py            # Shared foundations (vault, frontmatter, output, constants)
├── tasks.py           # Task CRUD, lifecycle, discovery, formatting
├── run.py             # Agent operations + run orchestration
├── init.py            # Init subcommand (self-contained)
└── cli.py             # Entry point: argparse + dispatch
```

### Import Graph

```
cli.py ──→ core.py
  │    ──→ tasks.py ──→ core.py
  │    ──→ run.py   ──→ core.py
  │    │              ──→ tasks.py
  │    ──→ init.py  ──→ core.py
```

All arrows point downward/sideways — no circular dependencies.
`core.py` is a leaf with no internal imports.

---

## Module Details

### 1. `core.py` — Shared Foundations

**Responsibility**: Vault discovery, frontmatter parsing, output
helpers, path utilities, constants. Everything that multiple
modules need.

**Constants**:
- `VERSION` (read from `__init__.py` or embedded)
- `EXIT_OK`, `EXIT_USAGE`, `EXIT_NO_PROJECT`, `EXIT_NOT_FOUND`,
  `EXIT_AMBIGUOUS`, `EXIT_TASK_NOT_READY`, `EXIT_INVALID_TRANSITION`,
  `EXIT_NO_CLAUDE`, `EXIT_AGENT_ERROR`, `EXIT_SOURCE_GUARD`
- `VALID_TRANSITIONS`, `VALID_STATUSES`
- `_STATUS_RANK`, `_MIN_PARENT_STATUS`

**Functions** (25):

| Function | Lines (current) | Notes |
|----------|----------------|-------|
| `find_root(start)` | 62–80 | Vault root discovery |
| `parse_frontmatter(text)` | 83–95 | Simple YAML parser |
| `parse_multiline_value(text, key)` | 98–118 | Folded/literal blocks |
| `parse_frontmatter_list(text, key)` | 572–592 | YAML list fields |
| `parse_frontmatter_for_json(text)` | 609–621 | JSON-suitable frontmatter |
| `extract_body(text)` | 595–606 | Body after frontmatter |
| `strip_wikilink(value)` | 564–569 | Strip `[[]]` syntax |
| `tasks_dir_path(root, prefix)` | 466–470 | Path helper |
| `slugify(description, max_words)` | 768–773 | Kebab-case conversion |
| `title_from_description(description)` | 776–786 | H1 title derivation |
| `err(msg)` | 58–59 | Error output to stderr |
| `info(msg)` | 660–663 | Info output to stderr |
| `_use_color()` | 672–673 | ANSI detection |
| `_green(s)` | 676 | Color helper |
| `_red(s)` | 677 | Color helper |
| `_bold(s)` | 678 | Color helper |
| `_dim(s)` | 679 | Color helper |
| `_ts()` | 682–687 | Timestamp prefix |
| `header(text)` | 690–696 | Section separator |
| `step(n, total, name)` | 699–703 | Step indicator |
| `detail(label, value)` | 706–710 | Indented detail |
| `success(msg)` | 713–717 | Green checkmark |
| `failure(msg)` | 720–722 | Red cross |
| `remaining_line(msg)` | 725–729 | Bullet point |
| `hint(msg)` | 732–736 | Dim hint |
| `format_duration(seconds)` | 739–744 | Time formatting |
| `summary_block(...)` | 747–762 | Run summary |
| `shlex_join(cmd)` | 1032–1035 | Shell-safe join |

**Module-level state**:
- `_quiet` flag (set by run module via setter)
- `_run_start` timestamp (set by run module via setter)

**Public API**:
```python
# Vault
def find_root(start=None) -> tuple[Path | None, str | None]: ...
def tasks_dir_path(root, prefix) -> Path: ...

# Frontmatter
def parse_frontmatter(text: str) -> dict: ...
def parse_multiline_value(text: str, key: str) -> str: ...
def parse_frontmatter_list(text: str, key: str) -> list[str]: ...
def parse_frontmatter_for_json(text: str) -> dict: ...
def extract_body(text: str) -> str: ...
def strip_wikilink(value: str) -> str: ...

# Text
def slugify(description: str, max_words: int = 5) -> str: ...
def title_from_description(description: str, max_len: int = 80) -> str: ...
def shlex_join(cmd: list[str]) -> str: ...

# Output (all print to stderr)
def set_quiet(value: bool) -> None: ...
def set_run_start(value: float | None) -> None: ...
def err(msg: str) -> None: ...
def info(msg: str) -> None: ...
def header(text: str) -> None: ...
def step(n: int, total: int, name: str) -> None: ...
def detail(label: str, value: str) -> None: ...
def success(msg: str) -> None: ...
def failure(msg: str) -> None: ...
def remaining_line(msg: str) -> None: ...
def hint(msg: str) -> None: ...
def format_duration(seconds: float) -> str: ...
def summary_block(completed, failed, pending, resume_cmd=None, next_task=None) -> None: ...
```

---

### 2. `tasks.py` — Task Operations

**Responsibility**: Task discovery, listing, showing, creating,
status transitions, resolution, formatting, and tree operations.

**Imports**: `from openstation import core`

**Functions** (22):

| Function | Lines (current) | Notes |
|----------|----------------|-------|
| `discover_tasks(root, prefix)` | 185–212 | Scan task files |
| `group_tasks_for_display(tasks)` | 215–256 | Parent/child grouping |
| `format_table(rows)` | 262–299 | Aligned table output |
| `collect_task_tree(tasks, root_name)` | 302–325 | Subtree collection |
| `pull_in_subtasks(filtered, all_tasks)` | 328–354 | Include descendants |
| `resolve_task(root, prefix, query)` | 421–460 | Name resolution |
| `find_ready_subtasks(tasks_dir, name, force)` | 624–654 | Ready subtask finder |
| `validate_transition(current, target)` | 831–836 | Lifecycle validation |
| `allowed_from(status)` | 839–841 | Reachable statuses |
| `auto_promote_parent(tasks_dir, name, status)` | 851–906 | Parent auto-promotion |
| `update_frontmatter(file_path, old, new)` | 909–917 | Status field update |
| `append_frontmatter_list(file_path, key, value)` | 920–963 | List field append |
| `assert_task_ready(spec_path, task_name)` | 553–561 | Status check |
| `next_task_id(tasks_dir)` | 789–798 | ID generation |
| `create_task_file(tasks_dir, slug, content)` | 801–828 | Atomic file creation |
| `cmd_list(args, root, prefix)` | 357–418 | List subcommand handler |
| `cmd_show(args, root, prefix)` | 1241–1272 | Show subcommand handler |
| `cmd_create(args, root, prefix)` | 1275–1366 | Create subcommand handler |
| `cmd_status(args, root, prefix)` | 1369–1421 | Status subcommand handler |

**Constants**:
- `SUBTASK_PREFIX` (`"  └─"`)
- `MAX_CREATE_RETRIES` (5)

**Public API**:
```python
# Discovery
def discover_tasks(root, prefix) -> list[dict]: ...
def resolve_task(root, prefix, query) -> tuple[str | None, str | None, int]: ...
def find_ready_subtasks(tasks_dir, task_name, force=False) -> list[tuple]: ...
def assert_task_ready(spec_path, task_name) -> tuple[bool, str]: ...

# Lifecycle
def validate_transition(current: str, target: str) -> bool: ...
def allowed_from(status: str) -> set[str]: ...
def auto_promote_parent(tasks_dir, task_name, child_new_status) -> str | None: ...
def update_frontmatter(file_path, old_status, new_status) -> None: ...
def append_frontmatter_list(file_path, key, value) -> None: ...

# Formatting
def group_tasks_for_display(tasks) -> list[tuple]: ...
def format_table(rows) -> str: ...
def collect_task_tree(tasks, root_name) -> list[dict]: ...
def pull_in_subtasks(filtered_tasks, all_tasks) -> list[dict]: ...

# Write helpers
def next_task_id(tasks_dir) -> str: ...
def create_task_file(tasks_dir, slug, content) -> Path: ...

# Command handlers
def cmd_list(args, root, prefix) -> int: ...
def cmd_show(args, root, prefix) -> int: ...
def cmd_create(args, root, prefix) -> int: ...
def cmd_status(args, root, prefix) -> int: ...
```

---

### 3. `run.py` — Agent Operations + Run Orchestration

**Responsibility**: Agent discovery and formatting, agent spec
parsing, command building, and the `run` subcommand (by-agent
and by-task modes).

**Imports**: `from openstation import core, tasks`

**Functions** (11):

| Function | Lines (current) | Notes |
|----------|----------------|-------|
| `discover_agents(root, prefix)` | 121–147 | Scan agent specs |
| `format_agents_table(agents)` | 150–173 | Agent table formatting |
| `find_agent_spec(root, prefix, name)` | 473–487 | Locate agent spec |
| `parse_allowed_tools(spec_path)` | 490–520 | Extract tools list |
| `build_command(agent, tier, ...)` | 523–550 | CLI argv assembly |
| `run_single_task(root, prefix, ...)` | 966–1029 | Execute one task |
| `_exec_or_run(root, prefix, ...)` | 1181–1238 | Exec when no queue |
| `cmd_agents(args, root, prefix)` | 176–182 | Agents subcommand |
| `cmd_run(args, root, prefix)` | 1038–1178 | Run subcommand |

**Constants**:
- `DEFAULT_TIER`, `DEFAULT_BUDGET`, `DEFAULT_TURNS`, `DEFAULT_MAX_TASKS`

**Public API**:
```python
# Agent operations
def discover_agents(root, prefix) -> list[dict]: ...
def format_agents_table(agents) -> str: ...
def find_agent_spec(root, prefix, agent_name) -> Path | None: ...
def parse_allowed_tools(spec_path) -> list[str]: ...
def build_command(agent_name, tier, budget, turns, prompt, tools, output_format="json") -> list[str]: ...

# Execution
def run_single_task(root, prefix, task_spec, task_name, tier, budget, turns, dry_run, json_output=False) -> int: ...

# Command handlers
def cmd_agents(args, root, prefix) -> int: ...
def cmd_run(args, root, prefix) -> int: ...
```

---

### 4. `init.py` — Init Subcommand

**Responsibility**: The `openstation init` command — directory
creation, file copying, agent template installation, symlink
creation. Self-contained; only imports from `core`.

**Imports**: `from openstation import core`

**Functions** (10):

| Function | Lines (current) | Notes |
|----------|----------------|-------|
| `_InitStats` class | 1481–1485 | Stats counter |
| `_init_info(msg, dry_run)` | 1488–1490 | Init success output |
| `_init_skip(msg, dry_run)` | 1493–1495 | Init skip output |
| `_init_warn(msg)` | 1498–1499 | Init warning |
| `_init_err(msg)` | 1502–1503 | Init error |
| `_copy_from_cache(src, dst, dir, dry)` | 1506–1516 | File copy |
| `_discover_templates(source_dir)` | 1519–1524 | Agent template scan |
| `_get_project_name()` | 1527–1539 | Project name from CLAUDE.md |
| `_adapt_template(content, name)` | 1542–1550 | Template adaptation |
| `_install_agents(...)` | 1553–1599 | Agent installation |
| `_create_claude_symlinks(dry_run)` | 1602–1673 | Symlink creation |
| `cmd_init(args)` | 1676–1798 | Init subcommand handler |

**Constants**:
- `OPENSTATION_HOME`
- `INIT_DIRS`, `INIT_GITKEEP_DIRS`, `INIT_COMMANDS`,
  `INIT_SKILLS`, `INIT_DOCS`, `INIT_DEFAULT_AGENTS`

**Public API**:
```python
def cmd_init(args) -> int: ...
```

---

### 5. `cli.py` — Entry Point

**Responsibility**: Argparse definition, subcommand routing, and
the `main()` function. Thin dispatcher — no business logic.

**Imports**: `from openstation import core, tasks, run, init`

**Functions** (1):

| Function | Lines (current) | Notes |
|----------|----------------|-------|
| `main()` | 1801–1968 | Argparse + dispatch |

**Public API**:
```python
def main() -> int: ...
```

---

### 6. `__init__.py` — Package Marker

```python
"""OpenStation CLI — manage the Open Station task vault."""

__version__ = "0.6.1"  # or read from .version at build time
```

Version handling changes: instead of `_read_version()` walking
up from `__file__` to find `.version`, the version is either
baked in at build time (zipapp) or read from a `_version.py`
generated by the build script. For development, `__init__.py`
can fall back to reading `.version`:

```python
def _read_version():
    try:
        from pathlib import Path
        vfile = Path(__file__).resolve().parent.parent.parent / ".version"
        return vfile.read_text(encoding="utf-8").strip()
    except Exception:
        return "dev"

__version__ = _read_version()
```

---

## Entry Point Wrapper

`bin/openstation` becomes a thin development wrapper:

```python
#!/usr/bin/env python3
"""Development entry point — adds src/ to sys.path and runs the CLI."""
import sys
from pathlib import Path

# Add src/ to path for running from a git checkout
src = Path(__file__).resolve().parent.parent / "src"
if src.is_dir():
    sys.path.insert(0, str(src))

from openstation.cli import main
sys.exit(main())
```

This keeps `bin/openstation` functional for development (running
from a git checkout without installation). The zipapp and pip
entry points use `openstation.cli:main` directly.

---

## Distribution (from task 0085 research)

Per the research in `artifacts/research/src-refactor-install-impact.md`:

**Primary: Zipapp**
```bash
python -m zipapp src/openstation \
  -m "openstation.cli:main" \
  -p "/usr/bin/env python3" \
  -o dist/openstation --compress
```

The `__main__.py` for zipapp:
```python
from openstation.cli import main
main()
```

**Secondary: pip install**

`pyproject.toml`:
```toml
[project]
name = "openstation"
version = "0.6.1"
requires-python = ">=3.9"

[project.scripts]
openstation = "openstation.cli:main"

[tool.setuptools.packages.find]
where = ["src"]
```

**install.sh**: Updated to symlink `dist/openstation` (zipapp)
instead of `bin/openstation`. Curl fallback downloads the
pre-built zipapp from GitHub releases.

---

## Test Migration Strategy

### Current State

`tests/test_cli.py` has 167 tests. All use subprocess invocation:

```python
CLI = str(Path(__file__).resolve().parent.parent / "bin" / "openstation")

def run_cli(args, cwd=None, env=None):
    result = subprocess.run(
        [sys.executable, CLI] + args, ...
    )
```

### Migration Approach

**Phase 1 — Keep subprocess tests working** (during refactor):

Update `run_cli` to invoke the module entry point:

```python
def run_cli(args, cwd=None, env=None):
    result = subprocess.run(
        [sys.executable, "-m", "openstation"] + args,
        capture_output=True, text=True, cwd=cwd, env=env,
    )
    return result.stdout, result.stderr, result.returncode
```

Add `src/openstation/__main__.py`:
```python
from openstation.cli import main
import sys
sys.exit(main())
```

Set `PYTHONPATH` in the test runner or `conftest.py`:
```python
# conftest.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
```

This keeps all 167 existing tests passing with minimal changes.

**Phase 2 — Add unit tests per module** (follow-up task):

New test files that import functions directly:

```
tests/
├── test_cli.py          # Existing integration tests (subprocess)
├── test_core.py         # Unit tests for frontmatter, vault, output
├── test_tasks.py        # Unit tests for task operations
├── test_run.py          # Unit tests for agent/run operations
└── test_init.py         # Unit tests for init
```

Direct imports enable faster tests and better isolation:
```python
from openstation.core import parse_frontmatter, slugify
from openstation.tasks import resolve_task, validate_transition
```

Phase 2 is a separate task — the refactor itself only needs
Phase 1 to maintain green tests.

---

## Function-to-Module Assignment (Complete)

Every function in `bin/openstation` mapped to its target module:

### core.py (27 functions + constants)

| Function | Current Line |
|----------|-------------|
| `_read_version()` | 18 |
| `err(msg)` | 58 |
| `find_root(start)` | 62 |
| `parse_frontmatter(text)` | 83 |
| `parse_multiline_value(text, key)` | 98 |
| `strip_wikilink(value)` | 564 |
| `parse_frontmatter_list(text, key)` | 572 |
| `extract_body(text)` | 595 |
| `parse_frontmatter_for_json(text)` | 609 |
| `info(msg)` | 660 |
| `_use_color()` | 672 |
| `_green(s)` | 676 |
| `_red(s)` | 677 |
| `_bold(s)` | 678 |
| `_dim(s)` | 679 |
| `_ts()` | 682 |
| `header(text)` | 690 |
| `step(n, total, name)` | 699 |
| `detail(label, value)` | 706 |
| `success(msg)` | 713 |
| `failure(msg)` | 720 |
| `remaining_line(msg)` | 725 |
| `hint(msg)` | 732 |
| `format_duration(seconds)` | 739 |
| `summary_block(...)` | 747 |
| `slugify(description, max_words)` | 768 |
| `title_from_description(description)` | 776 |
| `tasks_dir_path(root, prefix)` | 466 |
| `shlex_join(cmd)` | 1032 |

### tasks.py (19 functions)

| Function | Current Line |
|----------|-------------|
| `discover_tasks(root, prefix)` | 185 |
| `group_tasks_for_display(tasks)` | 215 |
| `format_table(rows)` | 262 |
| `collect_task_tree(tasks, root_name)` | 302 |
| `pull_in_subtasks(filtered, all)` | 328 |
| `cmd_list(args, root, prefix)` | 357 |
| `resolve_task(root, prefix, query)` | 421 |
| `assert_task_ready(spec_path, name)` | 553 |
| `find_ready_subtasks(dir, name, force)` | 624 |
| `next_task_id(tasks_dir)` | 789 |
| `create_task_file(tasks_dir, slug, content)` | 801 |
| `validate_transition(current, target)` | 831 |
| `allowed_from(status)` | 839 |
| `auto_promote_parent(dir, name, status)` | 851 |
| `update_frontmatter(path, old, new)` | 909 |
| `append_frontmatter_list(path, key, value)` | 920 |
| `cmd_show(args, root, prefix)` | 1241 |
| `cmd_create(args, root, prefix)` | 1275 |
| `cmd_status(args, root, prefix)` | 1369 |

### run.py (9 functions)

| Function | Current Line |
|----------|-------------|
| `discover_agents(root, prefix)` | 121 |
| `format_agents_table(agents)` | 150 |
| `cmd_agents(args, root, prefix)` | 176 |
| `find_agent_spec(root, prefix, name)` | 473 |
| `parse_allowed_tools(spec_path)` | 490 |
| `build_command(agent, tier, ...)` | 523 |
| `run_single_task(root, prefix, ...)` | 966 |
| `_exec_or_run(root, prefix, ...)` | 1181 |
| `cmd_run(args, root, prefix)` | 1038 |

### init.py (12 functions/classes)

| Function | Current Line |
|----------|-------------|
| `_InitStats` class | 1481 |
| `_init_info(msg, dry_run)` | 1488 |
| `_init_skip(msg, dry_run)` | 1493 |
| `_init_warn(msg)` | 1498 |
| `_init_err(msg)` | 1502 |
| `_copy_from_cache(src, dst, dir, dry)` | 1506 |
| `_discover_templates(source_dir)` | 1519 |
| `_get_project_name()` | 1527 |
| `_adapt_template(content, name)` | 1542 |
| `_install_agents(...)` | 1553 |
| `_create_claude_symlinks(dry_run)` | 1602 |
| `cmd_init(args)` | 1676 |

### cli.py (1 function)

| Function | Current Line |
|----------|-------------|
| `main()` | 1801 |

**Total: 68 functions + 1 class = all code accounted for.**

---

## Decisions

| Decision | Status | Rationale |
|----------|--------|-----------|
| 5 modules (core, tasks, run, init, cli) | **Decided** | Balanced — each module has a clear responsibility; fewer than 5 would bloat core; more than 5 would fragment small modules |
| Output helpers in core.py | **Decided** | Used by tasks, run, and init — centralizing avoids duplication or a 6th module for ~15 small functions |
| Agent operations in run.py | **Decided** | Only 5 agent functions, all consumed by run orchestration; a separate agents.py would be too thin |
| Mutable module state via setters | **Decided** | `_quiet` and `_run_start` are set once per run; setter functions are cleaner than passing through every call |
| Version in `__init__.py` | **Decided** | Standard Python packaging convention; fallback to `.version` file for dev |
| Phase 1 test migration only | **Decided** | Keeps refactor scope tight; unit test expansion is a follow-up task |
| Zipapp as primary distribution | **Decided** | Per task 0085 research — preserves single-file UX, stdlib-only build |
