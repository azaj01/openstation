---
kind: spec
name: cli-write-commands
agent: architect
task: "[[0051-cli-write-commands-spec]]"
created: 2026-03-05
status: final
---

# CLI Write Commands: `create` and `status`

Add two write subcommands to `bin/openstation` that allow
scriptable task creation and status transitions without an
LLM session.

## Problem

Creating tasks and changing statuses currently requires either
an active Claude session (slash commands) or manual frontmatter
editing. Agents and humans need scriptable write operations
usable in shell pipelines, CI, and automation — consistent with
the existing read-only CLI (`list`, `show`, `run`).

## Architecture

```
openstation create <description> [OPTIONS]
openstation status <task> <new-status>
│
├─ parse args
│
├─ find_root()                ← existing (shared with list/show/run)
│
├─ CREATE path
│   ├─ slugify()              ← new: description → kebab-case slug
│   ├─ build_frontmatter()    ← new: assemble YAML block
│   ├─ build_body()           ← new: assemble markdown body
│   └─ create_task_file()     ← new: next_task_id() + O_CREAT|O_EXCL + retry
│
└─ STATUS path
    ├─ resolve_task()         ← existing (shared with show/run)
    ├─ parse_frontmatter()    ← existing
    ├─ validate_transition()  ← new: check lifecycle.md rules
    └─ update_frontmatter()   ← new: rewrite status field in-place
```

### Data Flow — `create`

```
description string
      │
      ▼
  slugify()              ─► kebab-case, max 5 words, ASCII
      │
      ▼
  build_frontmatter()    ─► YAML block with kind, name, status, etc.
      │
      ▼
  build_body()           ─► # Title\n\n## Requirements\n\n...\n\n## Verification
      │
      ▼
  create_task_file()     ─► next_task_id() + O_CREAT|O_EXCL + retry
      │
      ▼
  print task name to stdout
```

### Data Flow — `status`

```
task query + new-status
      │
      ▼
  resolve_task()         ─► exact or prefix match → task name
      │
      ▼
  read task file         ─► parse current status from frontmatter
      │
      ▼
  validate_transition()  ─► check (current, target) against allowed pairs
      │
      ▼
  update_frontmatter()   ─► rewrite status line in file
      │
      ▼
  print confirmation to stdout
```

---

## Task ID Generation Mechanism

Requirement 3 asks for a robust ID mechanism that handles
concurrent creates without collisions and requires no external
services. This section evaluates alternatives.

### Alternatives Evaluated

**A. Filesystem scan + plain write** — Scan `artifacts/tasks/`,
find max numeric prefix, write `(max + 1)-slug.md`.

- ✓ Simple, no extra files
- ✗ Race condition: two concurrent creates scan the same max ID
  and one overwrites the other's file

**B. Filesystem scan + atomic create (`O_CREAT | O_EXCL`)** —
Same scan, but create the file with `os.open(path, O_CREAT |
O_EXCL | O_WRONLY)`. If the OS returns `EEXIST`, re-scan and
retry with the next available ID.

- ✓ OS-level atomicity prevents file collisions (POSIX guarantee)
- ✓ No extra files, no locking infrastructure
- ✓ Retry loop is bounded (at most N concurrent writers)
- ✓ Works on macOS and Linux identically
- ✗ Slightly more code than plain write (retry loop + fd management)

**C. Counter file with advisory locking** — Store next ID in
`artifacts/tasks/.next-id`, lock with `fcntl.flock()`, read →
increment → write → unlock.

- ✓ O(1) — no directory scan needed
- ✗ Extra file to maintain and version-control
- ✗ `fcntl.flock()` semantics vary across OS and filesystem type
- ✗ Risk of stale locks on process crash (requires cleanup logic)
- ✗ Adds a coordination file that is alien to the convention-over-
  database philosophy

**D. Timestamp / UUID-based IDs** — Use `YYYYMMDDHHMMSS` or
UUID4 as the ID prefix.

- ✓ Collision-free by design (no coordination needed)
- ✗ Breaks the 4-digit NNNN convention used everywhere
- ✗ Not human-friendly, not monotonically incrementing in a
  readable way
- ✗ Would require migrating every existing task and all docs

### Decision: Option B — Atomic file creation with retry

**Rationale:** Option B preserves the sequential NNNN convention,
handles concurrent creates through POSIX-standard `O_CREAT |
O_EXCL` atomicity, and adds no new infrastructure. The retry
loop adds ~15 lines of code. Options C and D introduce artifacts
or break conventions that are worse than the marginal complexity
of a retry loop. Option A is the "hope for the best" version of
B and has a real (if rare) data-loss risk.

### Implementation

```python
import os
import errno

MAX_CREATE_RETRIES = 5

def create_task_file(tasks_dir, slug, content):
    """Create a task file with the next available ID.

    Uses O_CREAT | O_EXCL for atomic creation. Retries on
    collision up to MAX_CREATE_RETRIES times.

    Returns the created Path, or raises RuntimeError.
    """
    for attempt in range(MAX_CREATE_RETRIES):
        next_id = next_task_id(tasks_dir)
        filename = f"{next_id}-{slug}.md"
        filepath = tasks_dir / filename
        try:
            fd = os.open(
                str(filepath),
                os.O_CREAT | os.O_EXCL | os.O_WRONLY,
                0o644,
            )
            with os.fdopen(fd, "w") as f:
                f.write(content)
            return filepath
        except OSError as e:
            if e.errno == errno.EEXIST:
                continue  # ID was claimed — re-scan and retry
            raise
    raise RuntimeError(
        f"Failed to create task after {MAX_CREATE_RETRIES} retries"
    )
```

The `next_task_id()` function (defined below in C1) scans the
directory each time it is called, so retries naturally pick up
the newly-created file from the concurrent writer.

---

## C1: `create` Subcommand

```
openstation create <description> [--agent NAME] [--owner NAME] [--status STATUS] [--parent TASK]
```

### Arguments

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `description` | string | yes | Free-text task description (used for title and slug) |

### Flags

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--agent` | string | empty | Agent name to assign |
| `--owner` | string | `user` | Who verifies (agent name or `user`) |
| `--status` | string | `backlog` | Initial status (`backlog` or `ready`) |
| `--parent` | string | empty | Parent task name (wikilink added automatically) |

### ID Assignment — `next_task_id()`

Called by `create_task_file()` (see Task ID Generation Mechanism)
on each attempt. Re-scans the directory every call so retries
see files created by concurrent writers.

1. List all `.md` files in `artifacts/tasks/`.
2. Extract the leading numeric prefix from each filename
   (regex: `^(\d+)-`).
3. Find the maximum numeric value.
4. Return `max + 1`, zero-padded to 4 digits.
5. If no task files exist, return `0001`.

```python
def next_task_id(tasks_dir):
    max_id = 0
    for entry in tasks_dir.iterdir():
        if entry.suffix != ".md":
            continue
        match = re.match(r"^(\d+)-", entry.name)
        if match:
            max_id = max(max_id, int(match.group(1)))
    return f"{max_id + 1:04d}"
```

File creation itself is handled by `create_task_file()` which
wraps `next_task_id()` with `O_CREAT | O_EXCL` atomicity and
retry. See "Task ID Generation Mechanism" above.

### Slug Generation — `slugify()`

1. Lowercase the description.
2. Replace non-alphanumeric characters with hyphens.
3. Collapse consecutive hyphens.
4. Strip leading/trailing hyphens.
5. Truncate to the first 5 words (split on `-`).
6. If the result is empty after processing, use `untitled`.

```python
def slugify(description, max_words=5):
    slug = re.sub(r"[^a-z0-9]+", "-", description.lower()).strip("-")
    slug = re.sub(r"-+", "-", slug)
    parts = slug.split("-")[:max_words]
    return "-".join(parts) or "untitled"
```

### File Format

The generated file follows `docs/task.spec.md` exactly:

```markdown
---
kind: task
name: NNNN-slug
status: backlog
agent:
owner: user
created: YYYY-MM-DD
---

# Title From Description

## Requirements

<description text>

## Verification

- [ ] (placeholder)
```

When `--parent` is provided, add:
```yaml
parent: "[[parent-task-name]]"
```

When `--agent` is provided, populate the `agent:` field.
When `--status ready` is provided, set `status: ready`.

### Title Generation

The H1 title is derived from the description:
1. Take the raw description string.
2. Title-case it.
3. Truncate to 80 characters if longer (no mid-word truncation).

### Output

On success, print the created task name to stdout:

```
0052-my-new-task
```

This enables shell composition: `openstation show $(openstation create "my new task")`

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Task created successfully |
| 1 | Usage error (missing description, invalid --status value) |
| 2 | Not in an Open Station project |

---

## C2: `status` Subcommand

```
openstation status <task> <new-status>
```

### Arguments

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `task` | string | yes | Task ID or slug (same resolution as `show`) |
| `new-status` | string | yes | Target status value |

### Valid Transitions — `validate_transition()`

Per `docs/lifecycle.md`:

```python
VALID_TRANSITIONS = {
    ("backlog", "ready"),
    ("ready", "in-progress"),
    ("in-progress", "review"),
    ("review", "done"),
    ("review", "failed"),
    ("failed", "in-progress"),
}
```

The function takes `(current_status, target_status)` and returns
`True` if the pair is in `VALID_TRANSITIONS`, `False` otherwise.

### Frontmatter Update — `update_frontmatter()`

1. Read the entire task file.
2. Find the line matching `status: <current>` within the
   frontmatter block (between `---` delimiters).
3. Replace it with `status: <target>`.
4. Write the file back.

This preserves all other frontmatter fields and the markdown
body unchanged. The update is a single-line replacement — no
full YAML serialization.

```python
def update_frontmatter(file_path, old_status, new_status):
    text = file_path.read_text(encoding="utf-8")
    # Only replace within frontmatter (between --- markers)
    updated = text.replace(
        f"status: {old_status}",
        f"status: {new_status}",
        1,  # replace first occurrence only
    )
    file_path.write_text(updated, encoding="utf-8")
```

### Parent Task Side-effects

When `--parent` is used with `create`, both directions of the
parent/child relationship are updated in a single invocation:

1. Resolve the parent task via `resolve_task()`.
2. Verify the parent exists (exit 3 if not).
3. Add `parent: "[[parent-name]]"` to the new task's frontmatter.
4. Append `"[[NNNN-slug]]"` to the parent's `subtasks` frontmatter
   list via `append_frontmatter_list()`.
5. If the parent has no `subtasks:` field yet, insert one before
   the closing `---` of the frontmatter block.

This ensures both the child's `parent` field and the parent's
`subtasks` list are consistent after a single `create` call,
per `docs/storage-query-layer.md` § 5.

#### `append_frontmatter_list()` — New Helper

Appends a value to a YAML list field in frontmatter. Handles
two cases: (a) the field already exists with list items, and
(b) the field does not exist yet.

```python
def append_frontmatter_list(file_path, key, value):
    """Append a value to a YAML list field in frontmatter.

    If the field exists, appends after the last list item.
    If the field does not exist, inserts it before the closing ---.
    """
    text = file_path.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    new_item = f'  - "{value}"\n'

    # Find frontmatter boundaries
    fm_start = None
    fm_end = None
    for i, line in enumerate(lines):
        if line.strip() == "---":
            if fm_start is None:
                fm_start = i
            else:
                fm_end = i
                break

    if fm_start is None or fm_end is None:
        raise ValueError(f"No frontmatter found in {file_path}")

    # Look for existing field within frontmatter
    field_line = None
    last_list_item = None
    for i in range(fm_start + 1, fm_end):
        if lines[i].startswith(f"{key}:"):
            field_line = i
        elif field_line is not None and re.match(r"^\s+-\s+", lines[i]):
            last_list_item = i
        elif field_line is not None and not re.match(r"^\s+-\s+", lines[i]):
            break  # Left the list block

    if field_line is not None and last_list_item is not None:
        # Append after the last list item
        lines.insert(last_list_item + 1, new_item)
    elif field_line is not None:
        # Field exists but has no items (e.g., "subtasks:")
        lines.insert(field_line + 1, new_item)
    else:
        # Field does not exist — insert before closing ---
        lines.insert(fm_end, f"{key}:\n")
        lines.insert(fm_end + 1, new_item)

    file_path.write_text("".join(lines), encoding="utf-8")
```

**Why this is safe:** The function operates on individual lines,
not a full YAML parse. It only inserts — it never modifies or
removes existing lines. The existing `parse_frontmatter_list()`
already reads list fields with the same line-by-line approach,
so the write counterpart is consistent. The frontmatter
boundaries (`---`) provide a reliable scope guard.

#### Parent body section

The `## Subtasks` body section is **not** updated by the CLI.
Body-section editing requires Markdown structural awareness
that is out of scope for the CLI. Agents and humans add
sub-task descriptions to the body section manually. The
frontmatter `subtasks` list is the machine-readable source
of truth; the body section is supplementary documentation.

### Output

On success, print a confirmation to stdout:

```
0052-my-new-task: backlog → ready
```

On no-op (already at target status), print:

```
0052-my-new-task: already at ready
```

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Status updated (or already at target) |
| 1 | Usage error (missing arguments) |
| 2 | Not in an Open Station project |
| 3 | Task not found |
| 4 | Ambiguous task match |
| 5 | Invalid transition |

---

## Edge Cases

### `create` Edge Cases

**Duplicate slugs.** Two tasks can produce the same slug from
different descriptions ("add login" and "Add Login!" both → `add-login`).
This is not a conflict — the 4-digit ID prefix makes every
filename unique (`0052-add-login.md` vs `0053-add-login.md`).
No deduplication logic is needed.

**Empty description.** If the description is empty or produces
an empty slug after processing, use `untitled` as the slug.
Print `error: description required` and exit 1 if the positional
argument is missing entirely.

**Invalid --status value.** Only `backlog` and `ready` are
accepted for `--status`. Any other value prints
`error: --status must be 'backlog' or 'ready'` and exits 1.

**Invalid --parent value.** If `--parent` is provided but the
parent task cannot be resolved, print
`error: parent task not found: <value>` and exit 3.

**Parent subtasks update failure.** If the child task is created
successfully but appending to the parent's `subtasks` fails
(e.g., malformed frontmatter, write error), the child file
remains valid (its `parent` field is correct). Print a warning
to stderr: `warning: created NNNN-slug but failed to update
parent subtasks list`. Exit 0 (the primary operation succeeded).
The user can fix the parent manually.

**Parent already lists child.** If `append_frontmatter_list()`
is called but the value already exists in the list, it should
still append (idempotent dedup is not required — duplicate
entries in `subtasks` are harmless and unlikely in practice
since `create` generates unique task names).

**Concurrent ID collision.** Two concurrent `create` calls could
scan the same max ID. The atomic file creation mechanism
(`O_CREAT | O_EXCL`) detects this: the second writer gets
`EEXIST`, re-scans, and retries with the next ID. See "Task ID
Generation Mechanism" above. After `MAX_CREATE_RETRIES` (5)
failed attempts, the command exits with an error — this would
require 5+ simultaneous writers, which is not a realistic
scenario for this system.

### `status` Edge Cases

**Missing task.** If `resolve_task()` returns no match, print
`error: task not found: <query>` and exit 3. Same behavior as
`show`.

**Ambiguous task.** If `resolve_task()` returns multiple matches,
print the list and exit 4. Same behavior as `show`.

**Already at target status.** If the task's current status equals
the target status, print `NNNN-slug: already at <status>` and
exit 0. This is a no-op, not an error — idempotent behavior.

**Invalid transition.** If `(current, target)` is not in
`VALID_TRANSITIONS`, print a clear error:

```
error: invalid transition: backlog → done
       allowed from backlog: ready
```

The error message lists what transitions *are* allowed from
the current status. Exit 5.

**File write failure.** If the file cannot be written (e.g.,
permissions), print `error: cannot write task: <path>` and
exit 1.

---

## Components Summary

| # | Component | Location | Purpose |
|---|-----------|----------|---------|
| C1 | `create` command | `bin/openstation` | Create task files with auto-ID |
| C2 | `status` command | `bin/openstation` | Transition task status with validation |
| C3 | `create_task_file()` | (in C1) | Atomic file creation with retry (wraps `next_task_id`) |
| C4 | `next_task_id()` | (in C3) | Scan tasks dir for next available ID |
| C5 | `slugify()` | (in C1) | Description → kebab-case slug |
| C6 | `validate_transition()` | (in C2) | Check lifecycle rules |
| C7 | `update_frontmatter()` | (in C2) | In-place status field replacement |
| C8 | Integration tests | `tests/test_cli_write.py` | Subprocess-based tests |
| C9 | `append_frontmatter_list()` | (in C1) | Append item to YAML list field in frontmatter |

---

## Integration with Existing CLI

Both commands are added as new subcommands alongside `list`,
`show`, and `run` in the existing `main()` argparse structure.
They reuse:

- `find_root()` — vault root detection
- `resolve_task()` — task name resolution (for `status`)
- `parse_frontmatter()` — reading current field values
- `err()` / `info()` — error and info output helpers
- Exit code conventions from `cli-feature-spec.md`

No new dependencies are required — both commands use only
stdlib (`os`, `sys`, `re`, `pathlib`, `argparse`, `datetime`).

---

## Design Decisions

### DD-1: `status` not `transition` or `move`

The subcommand is named `status` because it directly maps to
the field being changed. `openstation status 0052 ready` reads
naturally as "set task 0052's status to ready."

### DD-2: Automatic parent subtasks update

When `--parent` is used with `create`, the CLI updates both
directions atomically: the child's `parent` field and the
parent's `subtasks` list. The new `append_frontmatter_list()`
helper uses line-by-line insertion (never modifying existing
lines), which is safe with the simple frontmatter parser.

If the parent update fails after the child is created, the
child file is still valid — the `parent` field is correct, and
the user receives an error message explaining the partial state.
This is preferable to a transactional rollback that would delete
the newly-created task file.

### DD-3: Idempotent no-op for same-status

`openstation status 0052 ready` when already `ready` exits 0
with a message. This supports scripting where the desired end
state matters more than whether a transition occurred.

### DD-4: Transition table is hardcoded

`VALID_TRANSITIONS` is a set of tuples in the source code,
mirroring `docs/lifecycle.md`. If lifecycle rules change,
the code must be updated. This is intentional — lifecycle
changes are rare and should be reviewed, not auto-detected.

### DD-5: Atomic file creation over counter file

`O_CREAT | O_EXCL` is preferred over a `.next-id` counter file
because: (a) it uses the filesystem as the coordination
mechanism — consistent with "convention over database"; (b) no
extra state file to version-control or risk stale locks;
(c) POSIX-standard, works identically on macOS and Linux. See
the alternatives analysis in "Task ID Generation Mechanism."

### DD-6: Output to stdout for composability

`create` prints just the task name. `status` prints a one-line
confirmation. Both are parseable by shell scripts. Informational
messages go to stderr via `info()`.

---

## Verification

| Component | Criterion |
|-----------|-----------|
| C1 | `openstation create "desc"` creates file in `artifacts/tasks/` |
| C1 | Created file has correct frontmatter per `task.spec.md` |
| C1 | `--agent`, `--owner`, `--status`, `--parent` flags work |
| C3/C4 | Auto-increment finds correct next ID |
| C3/C4 | First task in empty dir gets ID `0001` |
| C3 | Concurrent creates handled by atomic retry (no collision) |
| C5 | Slug is kebab-case, max 5 words |
| C5 | Special characters stripped, consecutive hyphens collapsed |
| C2 | `openstation status <task> <status>` updates frontmatter |
| C6 | All valid transitions accepted |
| C6 | Invalid transitions rejected with helpful error |
| C6 | Error message lists allowed transitions from current status |
| C7 | Only the `status:` line changes, rest of file preserved |
| C2 | Already-at-target prints no-op message, exits 0 |
| C2 | Missing task exits 3, ambiguous exits 4 |
| C9 | `--parent` appends `[[child]]` to parent's `subtasks` list |
| C9 | `--parent` creates `subtasks:` field if parent has none |
| C9 | Parent update failure does not delete the child task |
| C8 | Integration tests cover create and status happy paths |
| C8 | Integration tests cover edge cases (duplicates, invalid, no-op) |
| C8 | Integration tests cover `--parent` bidirectional linking |
