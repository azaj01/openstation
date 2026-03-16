---
kind: spec
name: hooks
---

# Hooks

Hooks run shell commands when a task's status changes. Use them
to enforce checks, send notifications, or automate workflows
around status transitions.

Hooks are **pre-transition** — they run after validation but
before the status is written to disk. If a hook fails, the
transition aborts and the task file is unchanged.

## Configuration

### Settings File

Hooks are defined in the project's settings file:

| Context | Path |
|---------|------|
| Installed project | `.openstation/settings.json` |
| Source repo | `settings.json` (vault root) |

If the file is missing or has no `hooks` key, no hooks fire.

### Schema

```json
{
  "hooks": {
    "StatusTransition": [
      {
        "matcher": "<pattern>",
        "command": "<shell command>",
        "timeout": 30
      }
    ]
  }
}
```

`StatusTransition` is an array. Each entry has:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `matcher` | string | yes | — | Transition pattern (see Matchers below) |
| `command` | string | yes | — | Shell command to run (`/bin/sh -c`) |
| `timeout` | integer | no | `30` | Max seconds before the hook is killed |

### Matchers

A matcher has the form `<old-status>→<new-status>`. Each side
is a literal status name or `*` (wildcard). The ASCII `->` is
also accepted.

| Pattern | Matches |
|---------|---------|
| `in-progress→review` | Exactly that transition |
| `*→done` | Any status → done |
| `review→*` | review → done or review → failed |
| `*→*` | Every transition (catch-all) |
| `*->done` | Same as `*→done` (ASCII alias) |

## Environment Variables

Hook commands receive task context via `OS_`-prefixed
environment variables:

| Variable | Description | Example |
|----------|-------------|---------|
| `OS_TASK_NAME` | Task name (no `.md`) | `0042-cli-improvements` |
| `OS_OLD_STATUS` | Status before transition | `in-progress` |
| `OS_NEW_STATUS` | Target status | `review` |
| `OS_TASK_FILE` | Absolute path to task file | `/home/user/project/.openstation/artifacts/tasks/0042-cli-improvements.md` |
| `OS_VAULT_ROOT` | Absolute path to vault root | `/home/user/project` |

All five variables are always set.

## Execution

### Ordering

Hooks fire in **declaration order** (array index in
`StatusTransition`). All matching hooks run unless one fails.

### Timing

```
validate status value
validate transition legality
─── hooks fire here ───
update_frontmatter()      ← only if all hooks pass
auto_promote_parent()
print confirmation
```

### Failure

If a hook exits non-zero:

1. Remaining hooks are **skipped**
2. The status transition is **aborted** (task file unchanged)
3. An error is printed: `hook failed: <command> (exit <code>)`
4. `openstation status` exits with code 10 (`EXIT_HOOK_FAILED`)

### Timeout

If a hook exceeds its timeout:

1. `SIGTERM` is sent
2. After 5 seconds, `SIGKILL` is sent if still running
3. Treated as a failure (transition aborted)
4. Error: `hook timed out after <N>s: <command>`

### Output

Hook stdout and stderr are inherited — output appears inline
in the terminal.

## Examples

### Lint before review

```json
{
  "hooks": {
    "StatusTransition": [
      {
        "matcher": "in-progress→review",
        "command": "bin/lint-task $OS_TASK_FILE"
      }
    ]
  }
}
```

### Notify on completion

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

### Log all transitions

```json
{
  "hooks": {
    "StatusTransition": [
      {
        "matcher": "*→*",
        "command": "echo \"$OS_TASK_NAME: $OS_OLD_STATUS → $OS_NEW_STATUS\" >> .openstation/hook.log"
      }
    ]
  }
}
```

### Multiple hooks

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

## Scope

Hooks fire only on `openstation status` transitions. They do
not fire on task creation, manual file edits, or slash commands
that edit frontmatter directly.

Features deferred for future work: post-transition hooks,
create-time hooks, dry-run mode, conditional hooks (filtering
by task fields), and structured output capture.

## Architecture

Internal design reference. For the full design spec see
`artifacts/specs/task-lifecycle-hooks.md`.

### Module Layout

All hook logic lives in `src/openstation/hooks.py`. Three
public functions form the API:

| Function | Purpose |
|----------|---------|
| `load_hooks(root, prefix)` | Read `StatusTransition` entries from `settings.json` |
| `match_hooks(hooks, old, new)` | Filter entries whose matcher matches the transition |
| `run_matched(root, prefix, task_name, old, new, task_file)` | Orchestrate: load → match → execute. Returns `None` on success, `EXIT_HOOK_FAILED` on failure. |

Private helpers: `_settings_path` resolves the settings file,
`_normalize_matcher` converts ASCII `->` to `→`,
`_run_hook` executes a single command via `subprocess.Popen`.

### Integration Point

Hooks are invoked from a single call site in `cmd_status()`
(`src/openstation/tasks.py`), between transition validation
and `update_frontmatter()`:

```
validate status value
validate transition legality
─── hooks.run_matched() ───      ← single call site
update_frontmatter()
auto_promote_parent()
print confirmation
```

This placement ensures hooks run after the transition is
validated but before the task file changes on disk.

### Data Flow

```
settings.json
  │
  ▼
load_hooks()        ← parse JSON, extract StatusTransition array
  │
  ▼
match_hooks()       ← filter by old→new pattern against each matcher
  │
  ▼
run_matched()       ← build OS_ env vars, run each hook via subprocess.Popen
  │                    stop on first failure
  ▼
None | EXIT_HOOK_FAILED (10)
```

### Exit Code

`EXIT_HOOK_FAILED = 10` is defined in `src/openstation/core.py`.
When `run_matched` returns this code, `cmd_status()` returns it
directly — the transition is aborted and the task file is unchanged.
