---
kind: spec
name: cli-feature-spec
task: 0023-cli-feature-spec
created: 2026-03-01
status: approved
---

# OpenStation CLI

Single-file Python CLI providing deterministic, scriptable
read-only access to the Open Station task vault.

## Problem

Slash commands (`/openstation.list`, `/openstation.show`) require
an active Claude session and produce non-deterministic output.
Agents and humans need a scriptable CLI that reads the vault
directly — usable in shell pipelines, CI, and without an LLM.

## Architecture

```
CLI invocation
│
├─ parse args ──► subcommand (list | show)
│
├─ find_root()
│   └─ walk up from CWD
│       ├─ .openstation/ dir → installed project (prefix=".openstation")
│       └─ agents/ + install.sh → source repo (prefix="")
│
├─ tasks_dir = root / prefix / "artifacts" / "tasks"
│
├─ LIST path
│   ├─ scan tasks_dir/*/index.md
│   ├─ parse_frontmatter() per file
│   ├─ resolve_bucket() via symlink check
│   ├─ apply filters (--status, --agent)
│   ├─ sort by ID ascending
│   └─ format_table() → stdout
│
└─ SHOW path
    ├─ resolve_task() by exact or prefix match
    ├─ read index.md
    └─ raw content → stdout
```

### Data Flow

```
artifacts/tasks/*/index.md
        │
        ▼
  parse_frontmatter()     ─► dict of key:value pairs
        │
        ▼
  resolve_bucket()        ─► check tasks/{backlog,current,done}/ symlinks
        │
        ▼
  filter + sort           ─► ordered task list
        │
        ▼
  format_table()          ─► stdout (list) or raw output (show)
```

### Vault Root Detection

Walk up from CWD to find the project root. Two detection patterns,
matching `openstation-run.sh`:

1. `.openstation/` directory → installed project (takes precedence)
2. `agents/` dir + `install.sh` file → source repo

Returns `(root_path, prefix)`. All paths derive from:
`tasks_dir = root / prefix / "artifacts" / "tasks"`

### Task Discovery

Scan `{tasks_dir}/*/index.md`. For each file:

1. Parse YAML frontmatter (between `---` delimiters)
2. Extract fields via `str.split(':', 1)` — no full YAML parser
3. Determine bucket by checking which symlink exists:
   - `tasks/backlog/NNNN-slug` → backlog
   - `tasks/current/NNNN-slug` → current
   - `tasks/done/NNNN-slug` → done
   - No symlink → orphan (sub-task or broken state)

### Frontmatter Parsing

Simple line-by-line parsing between `---` markers:

```
for each line between first --- and second ---:
    key, _, value = line.partition(':')
    fields[key.strip()] = value.strip()
```

Handles the flat `key: value` format used by task specs. Does not
handle nested YAML, multi-line values, or list fields beyond
`artifacts:` (which can be ignored for list/show).

## Components

| # | Component | Location | Purpose |
|---|-----------|----------|---------|
| C1 | CLI script | `bin/openstation` | Single-file Python 3.8+ entry point |
| C2 | `list` command | (in C1) | Filtered task table to stdout |
| C3 | `show` command | (in C1) | Raw task spec to stdout |
| C4 | Root detector | (in C1) | `find_root()` — walks up from CWD |
| C5 | Frontmatter parser | (in C1) | `parse_frontmatter()` — `str.split(':', 1)` |
| C6 | Bucket resolver | (in C1) | `resolve_bucket()` — checks symlinks |
| C7 | Integration tests | `tests/test_cli.py` | Subprocess-based tests with temp fixtures |

### C1: CLI Script

Single-file Python script with shebang (`#!/usr/bin/env python3`).
No package structure. External packages allowed when they add clear value.

**Source**: `bin/openstation`
**Installed**: `.openstation/bin/openstation` (copied by `install.sh`)

### C2: `list` Command

```
openstation list [--status <status>] [--agent <name>]
```

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--status` | string | `active` | Filter by status. Special: `active` (excludes done/failed), `all` (no filter) |
| `--agent` | string | none | Filter by agent name (exact match) |

**Output**: Formatted table to stdout.

```
ID     Name                         Status       Agent       Owner
----   --------------------------   ----------   ---------   -----
0021   openstation-cli              in-progress  researcher  manual
0023   cli-feature-spec             ready        architect   manual
```

- Column widths auto-sized to content, minimums: ID 4, Name 10, Status 7, Agent 5, Owner 5
- Sort: by ID ascending (numeric)
- Default: exclude `done`/`failed` (equivalent to `--status active`)
- Filters combine with AND

**Exit codes**: 0 success, 1 usage error, 2 not in project

### C3: `show` Command

```
openstation show <task>
```

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `task` | string | yes | Task ID (`0023`) or full slug (`0023-cli-feature-spec`) |

**Resolution**: match against folder names in `artifacts/tasks/`:
- Exact match: `0023-cli-feature-spec`
- Prefix match: `0023` matches `0023-cli-feature-spec`
- Multiple prefix matches → error with list of matches

**Output**: Raw content of `index.md` to stdout.

**Exit codes**: 0 success, 1 usage error, 2 not in project, 3 not found, 4 ambiguous

### C7: Integration Tests

Subprocess-based tests using `tempfile.mkdtemp()` to create
disposable vault structures. Each test creates minimal
directory/file fixtures, runs the CLI via `subprocess.run()`,
and asserts on stdout, stderr, and exit code.

**File**: `tests/test_cli.py`

**Categories**:

1. **List command** — default excludes done/failed, `--status`
   filters, `--agent` filters, combined filters, empty results,
   broken symlinks skipped
2. **Show command** — by slug, by ID prefix, ambiguous prefix
   (exit 4), not found (exit 3), missing index.md
3. **Root detection** — `.openstation/` in parent, source repo
   root, error when not in project

**Running**:
```bash
python3 -m pytest tests/test_cli.py        # if pytest available
python3 -m unittest tests.test_cli          # stdlib fallback
```

## Verification

| Component | Criterion |
|-----------|-----------|
| C1 | Script is executable with Python 3.8+ shebang |
| C2 | `openstation list` shows non-done tasks with status, agent, owner |
| C2 | `--status ready` filters correctly |
| C2 | `--status all` includes done/failed tasks |
| C2 | `--agent researcher` filters by agent |
| C2 | Combined filters work with AND logic |
| C3 | `openstation show <slug>` prints full task spec |
| C3 | `openstation show <id>` resolves prefix match |
| C3 | Ambiguous prefix → exit 4 with match list |
| C3 | Not found → exit 3 |
| C4 | Finds `.openstation/` in ancestor directory |
| C4 | Finds source repo root (agents/ + install.sh) |
| C4 | Errors when not in a project |
| C6 | Broken symlinks skipped silently in list |
| C6 | Missing index.md skipped in list, error in show |
| C7 | All test categories pass |

## Design Decisions

### DD-1: Single-file Python, not multi-module

One file at `bin/openstation` with no package structure. The CLI
has two commands and ~200 lines of logic — a package would add
complexity without benefit. Matches the `openstation-run.sh`
pattern of self-contained scripts.

### DD-2: Frontmatter parsing strategy

Frontmatter is parsed with `str.split(':', 1)` — handles the
flat `key: value` format used by task specs. A full YAML parser
(PyYAML) may be used if task specs grow to need nested YAML, list
fields, or multi-line values. For now the simple parser suffices.

### DD-3: Symlink-based bucket resolution

Instead of maintaining a status→bucket mapping, the CLI checks
which `tasks/{bucket}/` symlink exists for each task. This is
the source of truth — the symlink location defines the lifecycle
stage regardless of the frontmatter `status` field.

### DD-4: Read-only idempotency

Both commands are pure reads. Running them any number of times
produces identical output for the same vault state. No side effects.

### DD-5: Error format matches openstation-run.sh

All errors print `error: <message>` to stderr. No stack traces
or debug info. Consistent with the existing shell launcher.

## Error Handling

### Error Categories

| Code | Category | Examples |
|------|----------|---------|
| 0 | Success | Command completed (even with empty results) |
| 1 | Usage error | Missing arguments, invalid flags |
| 2 | Project error | Not in an Open Station project |
| 3 | Not found | Task not found (show only) |
| 4 | Ambiguous | Multiple tasks match a prefix (show only) |

### Edge Cases

**Broken symlinks**: `list` skips silently; `show` prints
`error: task folder missing (broken symlink)`.

**Missing `index.md`**: `list` skips the entry; `show` prints
`error: task spec missing`.

## Dependencies

| Dependency | Required | Purpose |
|------------|----------|---------|
| Python 3.8+ | yes | Runtime |
| `os`, `sys`, `pathlib` | yes | File system operations |
| `argparse` | yes | Argument parsing (stdlib) |
| `unittest`, `tempfile`, `subprocess` | test only | Integration tests |

External packages may be added via `requirements.txt` when they
provide clear value (e.g., `PyYAML` for robust frontmatter parsing,
`rich` for terminal formatting). Prefer stdlib when the stdlib
solution is adequate.
