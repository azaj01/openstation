---
kind: spec
name: cli-feature-spec
task: 0023-cli-feature-spec
created: 2026-03-01
---

# OpenStation CLI — Feature Spec

Technical specification for the `openstation` CLI tool. Based on
research from `0022-cli-feature-research`.

## Overview

A single-file Python 3.8+ CLI (`openstation`) that provides two
read-only commands: `list` and `show`. Replaces the prompt-driven
slash commands with deterministic, scriptable equivalents.
Uses stdlib only — no external dependencies.

---

## File Layout

### Source Location

```
bin/openstation          # Single-file Python script (source repo)
```

The script has a shebang (`#!/usr/bin/env python3`) and is
executable. No package structure — one file for the entire CLI.

### Installation

`install.sh` copies the script to the target project:

```
.openstation/bin/openstation
```

Users add `.openstation/bin` to their PATH, or invoke directly.

### Vault Root Detection

Walk up from CWD to find the project root. Matches the existing
`openstation-run.sh` pattern.

```
def find_root(start) -> (root_path, prefix):
    for each ancestor of start:
        if .openstation/ exists   → return (ancestor, ".openstation")
        if agents/ + install.sh  → return (ancestor, "")
    error: "not in an Open Station project"
```

**Precedence**: `.openstation/` wins if both are present (the
installed structure is canonical).

Once root and prefix are known, all paths derive from:

```
tasks_dir  = root / prefix / "artifacts" / "tasks"
```

---

## Task Discovery

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

---

## Commands

### `openstation list`

List tasks as a formatted table.

**Synopsis**:
```
openstation list [--status <status>] [--agent <name>]
```

**Flags**:

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--status` | string | `active` | Filter by status. Special values: `active` (excludes done/failed), `all` (no filter) |
| `--agent` | string | none | Filter by agent name (exact match) |

**Output**: Markdown table to stdout.

```
ID     Name                         Status       Agent       Owner
----   --------------------------   ----------   ---------   -----
0021   openstation-cli              in-progress  researcher  manual
0023   cli-feature-spec             ready        architect   manual
```

**Column widths**: Auto-sized to content, with minimum widths:
- ID: 4, Name: 10, Status: 7, Agent: 5, Owner: 5

**Sort order**: By ID ascending (numeric).

**Default behavior**: Exclude tasks with `status: done` or
`status: failed`. Equivalent to `--status active`.

**Filter logic**: Filters combine with AND. `--status ready
--agent researcher` shows only tasks that are both ready AND
assigned to researcher.

**Exit codes**:
- 0: Success (even if no tasks match)
- 1: Usage error (invalid flags)
- 2: Not in an Open Station project

---

### `openstation show`

Display the full task spec (frontmatter + body).

**Synopsis**:
```
openstation show <task>
```

**Arguments**:

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `task` | string | yes | Task ID (e.g., `0023`) or full slug (e.g., `0023-cli-feature-spec`) |

**Task resolution**: Match against folder names in `artifacts/tasks/`:
- Exact match: `0023-cli-feature-spec`
- Prefix match: `0023` matches `0023-cli-feature-spec`
- If multiple folders match a prefix, error with the list of matches

**Output**: Raw content of `index.md` to stdout.

**Exit codes**:
- 0: Success
- 1: Usage error (no task argument)
- 2: Not in an Open Station project
- 3: Task not found
- 4: Ambiguous match (multiple tasks match prefix)

---

## Error Handling

### Error Format

All errors print to stderr:

```
error: <message>
```

No stack traces or debug info in normal mode. Matches the
existing `openstation-run.sh` error format.

### Error Categories

| Code | Category | Examples |
|------|----------|---------|
| 0 | Success | Command completed (even with empty results) |
| 1 | Usage error | Missing arguments, invalid flags |
| 2 | Project error | Not in an Open Station project |
| 3 | Not found | Task not found |
| 4 | Ambiguous | Multiple tasks match a prefix |

### Broken Symlinks

When a bucket symlink points to a non-existent folder:
- `list`: Skip the entry silently (don't crash)
- `show`: Print `error: task folder missing (broken symlink)`

### Missing `index.md`

If a task folder exists but has no `index.md`:
- `list`: Skip the entry
- `show`: Print `error: task spec missing`

---

## Idempotency

Both commands are read-only. Running them any number of times
produces identical output for the same vault state. No side
effects.

---

## Testing Strategy

### Approach: Integration Tests with Temp Fixtures

Use Python `unittest` with `tempfile.mkdtemp()` to create
disposable vault structures. Each test creates the minimal
directory/file structure it needs, runs the CLI as a subprocess,
and asserts on stdout, stderr, and exit code.

### Test File Location

```
tests/test_cli.py       # All CLI tests in one file
```

Uses `subprocess.run()` to invoke `bin/openstation` as a child
process — tests the actual script, not imported functions.

### Test Categories

**1. List command**
- Default output excludes done/failed
- `--status ready` filters correctly
- `--status all` includes everything
- `--agent <name>` filters by agent
- Combined filters (`--status ready --agent researcher`)
- Empty result (no tasks match) → exit 0, empty table
- Broken symlinks are skipped

**2. Show command**
- Show by full slug
- Show by numeric ID prefix
- Ambiguous prefix (multiple matches) → exit 4
- Task not found → exit 3
- Missing index.md → error message

**3. Root detection**
- Finds `.openstation/` in parent directory
- Finds source repo root (agents/ + install.sh)
- Errors when not in a project

### Running Tests

```bash
python3 -m pytest tests/test_cli.py        # if pytest available
python3 -m unittest tests.test_cli          # stdlib fallback
```

Both work — no pytest dependency required.
