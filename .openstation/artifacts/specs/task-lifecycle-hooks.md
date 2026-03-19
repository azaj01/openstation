---
kind: spec
name: task-lifecycle-hooks
agent: architect
task: "[[0135-hooks-spec-design-configuration-schema]]"
created: 2026-03-15
---

# Task Lifecycle Hooks

Hooks allow users to run arbitrary commands when a task's status
changes. A hook fires **before** the status is written to disk
(pre-transition). If any hook exits non-zero, the transition
aborts and the task file is left unchanged.

Scope: status transitions triggered by `openstation status` only.
Post-transition hooks, create-time hooks, dry-run mode, and
structured output capture are deferred.

---

## 1. Configuration Schema

### 1.1 File Location

Hooks are configured in the project's Open Station settings file:

| Context | Path |
|---------|------|
| Installed project | `.openstation/settings.json` |
| Source repo | `settings.json` (vault root) |

The settings file is discovered relative to the vault root
returned by `find_root()`. If the file does not exist or contains
no `hooks` key, no hooks fire — this is not an error.

### 1.2 JSON Structure

```json
{
  "hooks": {
    "StatusTransition": [
      {
        "matcher": "*→review",
        "command": "echo 'entering review'",
        "timeout": 30
      }
    ]
  }
}
```

Top-level key: `hooks`. Sub-key: `StatusTransition` (array).
Other hook categories (e.g., `TaskCreate`) may be added later
under the same `hooks` parent without schema changes.

### 1.3 Entry Fields

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `matcher` | string | yes | — | Status transition pattern (see § 2) |
| `command` | string | yes | — | Shell command to execute |
| `timeout` | integer | no | `30` | Max seconds before the process is killed |

- `command` is passed to the system shell (`/bin/sh -c` on
  Unix). It may reference environment variables (see § 3).
- `timeout` must be a positive integer. Values ≤ 0 are treated
  as the default (30).

### 1.4 Minimal Example

```json
{
  "hooks": {
    "StatusTransition": [
      {
        "matcher": "*→done",
        "command": "notify-send 'Task $OS_TASK_NAME completed'"
      }
    ]
  }
}
```

### 1.5 Multi-Hook Example

```json
{
  "hooks": {
    "StatusTransition": [
      {
        "matcher": "in-progress→review",
        "command": "bin/lint-task $OS_TASK_FILE"
      },
      {
        "matcher": "*→done",
        "command": "bin/archive-task $OS_TASK_NAME",
        "timeout": 60
      },
      {
        "matcher": "*→*",
        "command": "echo \"$OS_TASK_NAME: $OS_OLD_STATUS → $OS_NEW_STATUS\" >> .openstation/hook.log"
      }
    ]
  }
}
```

---

## 2. Matcher Format

### 2.1 Syntax

```
<old-status>→<new-status>
```

Each side is either a literal status name or `*` (wildcard,
matches any status). The arrow is the Unicode character `→`
(U+2192). The ASCII alias `->` is also accepted and normalized
to `→` at parse time.

### 2.2 Matching Rules

A hook matches a transition `(current, new)` when:

1. The left side equals `current` **or** is `*`
2. The right side equals `new` **or** is `*`

Both sides must match for the hook to fire.

### 2.3 Pattern Examples

| Pattern | Matches |
|---------|---------|
| `in-progress→review` | Exactly that transition |
| `*→done` | Any status → done |
| `review→*` | review → done, review → failed |
| `*→*` | Every transition (catch-all) |
| `*->done` | Same as `*→done` (ASCII alias) |

### 2.4 Rationale: No Regex

The valid transition set is small (7 transitions). A
`left→right` pattern with wildcards covers every useful
combination without the complexity and error surface of regex.

---

## 3. Environment Variables

Hook commands receive task context via environment variables.
All variables use the `OS_` prefix (Open Station).

| Variable | Value | Example |
|----------|-------|---------|
| `OS_TASK_NAME` | Resolved task name (no `.md`) | `0042-cli-improvements` |
| `OS_OLD_STATUS` | Current status before transition | `in-progress` |
| `OS_NEW_STATUS` | Target status after transition | `review` |
| `OS_TASK_FILE` | Absolute path to the task file | `/home/user/project/.openstation/artifacts/tasks/0042-cli-improvements.md` |
| `OS_VAULT_ROOT` | Absolute path to the vault root | `/home/user/project` |

Variables are set in the hook subprocess environment. They do
**not** modify the parent process environment.

### 3.1 Variable Availability

All five variables are always set for every hook invocation.
None are optional. If a variable cannot be determined (which
should not happen after validation), the transition aborts
before any hooks run.

---

## 4. Execution Semantics

### 4.1 Timing: Pre-Transition

Hooks run **after** the transition is validated (status value
check, transition legality check) but **before**
`update_frontmatter()` writes the new status to disk.

```
validate status value
validate transition legality
─── hooks fire here ───
update_frontmatter()      ← only if all hooks pass
auto_promote_parent()
print confirmation
```

Rationale: pre-transition hooks can enforce additional
invariants (lint checks, required fields) and abort the
transition cleanly. The task file is never left in a partially
updated state.

### 4.2 Ordering

Hooks fire in **declaration order** — the array index in
`StatusTransition` determines sequence. All matching hooks
run unless one fails.

### 4.3 Synchronous Execution

Each hook runs to completion before the next starts. There is
no parallel execution. This keeps behavior deterministic and
makes failure semantics simple.

### 4.4 Failure Behavior

If a hook command exits with a **non-zero exit code**:

1. The transition **aborts immediately** — remaining hooks
   are skipped.
2. `update_frontmatter()` is **not called** — the task file
   is unchanged.
3. `cmd_status()` prints an error message:
   ```
   hook failed: <command> (exit <code>)
   ```
4. `cmd_status()` returns `EXIT_HOOK_FAILED` (10).

### 4.5 Timeout Handling

Each hook has a timeout (default 30 seconds, configurable per
entry). If the timeout expires:

1. Send `SIGTERM` to the process.
2. Wait 5 seconds for graceful shutdown.
3. If still running, send `SIGKILL`.
4. Treat as a failure (non-zero exit). The error message:
   ```
   hook timed out after <N>s: <command>
   ```

Use `subprocess.Popen` with a poll loop or
`subprocess.run(timeout=...)` with SIGKILL follow-up.

### 4.6 Output Handling

Hook stdout and stderr are **inherited** from the parent
process (not captured). Users see hook output inline in their
terminal. This matches the principle of least surprise for
shell commands.

---

## 5. CLI Integration

### 5.1 Insertion Point

The hook engine is called from a **single location**:
`tasks.py:cmd_status()`, between transition validation and
`update_frontmatter()`.

Current code (lines 659–670):

```python
if not validate_transition(current, new_status):
    ...
    return core.EXIT_INVALID_TRANSITION

try:
    update_frontmatter(spec, current, new_status)
except OSError:
    ...
```

After integration:

```python
if not validate_transition(current, new_status):
    ...
    return core.EXIT_INVALID_TRANSITION

# --- Hook execution (pre-transition) ---
hook_err = hooks.run_matched(root, prefix, task_name, current, new_status, spec)
if hook_err:
    return hook_err

try:
    update_frontmatter(spec, current, new_status)
except OSError:
    ...
```

No other commands (`create`, `show`, `list`) invoke hooks.
Only `cmd_status()` — which handles all status transitions
including those called by slash commands that shell out to
`openstation status`.

### 5.2 New Module: `hooks.py`

Location: `src/openstation/hooks.py`

Three public functions:

```python
def load_hooks(root: Path, prefix: str) -> list[dict]:
    """Read StatusTransition hooks from settings.json.

    Returns an empty list if the file is missing, has no
    'hooks' key, or has no 'StatusTransition' key. Raises
    no exceptions for missing/empty config.
    """

def match_hooks(hooks: list[dict], old: str, new: str) -> list[dict]:
    """Filter hooks whose matcher matches the (old, new) pair.

    Returns matching hooks in declaration order.
    """

def run_matched(
    root: Path, prefix: str,
    task_name: str, old: str, new: str, task_file: Path,
) -> int | None:
    """Load, match, and execute hooks for a transition.

    Returns None on success (all hooks passed or no hooks matched).
    Returns EXIT_HOOK_FAILED (10) if any hook fails or times out.
    """
```

### 5.3 New Exit Code

Add to `core.py`:

```python
EXIT_HOOK_FAILED = 10
```

Value 10 is chosen to leave room between the current highest
code (9, `EXIT_SOURCE_GUARD`) and future additions.

### 5.4 Settings File Discovery

```python
def _settings_path(root: Path, prefix: str) -> Path:
    """Return the settings file path for the vault."""
    return root / prefix / "settings.json" if prefix else root / "settings.json"
```

For installed projects (`prefix = ".openstation"`), this
yields `.openstation/settings.json`. For the source repo
(`prefix = ""`), it yields `settings.json` at vault root.

---

## 6. Scope Exclusions

The following are explicitly **not** part of this spec.
They may be addressed in future work:

| Feature | Rationale |
|---------|-----------|
| **Post-transition hooks** | Adds complexity (two hook phases). Can be added later with a `phase: pre/post` field. |
| **Create-time hooks** | Different trigger (no old status). Needs its own matcher design. |
| **Dry-run mode** | Useful but orthogonal. Can be added as a `--dry-run` flag on `openstation status`. |
| **Structured output capture** | Hooks are fire-and-forget shell commands. Capturing JSON output adds parsing complexity. |
| **Hook-specific working directory** | Hooks inherit CWD from the CLI invocation. Explicit `cwd` field can be added later. |
| **Conditional hooks** | Filtering by task fields (assignee, type). Adds matcher complexity. Defer until there's demand. |
