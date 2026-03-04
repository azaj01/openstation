---
kind: task
name: 0030-task-selection-modes
status: done
agent: author
owner: manual
created: 2026-03-01
---

# Fix Task Selection — Two Execution Modes

## Requirements

The current `openstation-run.sh` conflates agent resolution with
task execution. Both `<agent-name>` and `--task` resolve to an
agent name, then launch that agent identically. The `--task` path
should instead enable task-driven execution with subtask
orchestration.

### R1: By-Agent Mode (existing, unchanged)

```
openstation-run.sh <agent-name> [OPTIONS]
```

Agent name is given directly. The agent launches, finds its own
ready tasks via the `openstation-execute` skill, and executes them.
This is the current behavior — no changes needed.

### R2: By-Task Mode (new)

```
openstation-run.sh --task <id-or-slug> [OPTIONS]
```

When `--task` is provided:

1. **Survey the task** — read its `index.md`, check `status` is
   `ready` (exit with error if not).
2. **Check for subtasks** — scan for symlinked sub-task folders
   inside the task directory. Read each sub-task's `index.md`.
3. **Execute subtasks** — for each sub-task that is `ready`:
   - Resolve the sub-task's `agent` field.
   - Launch the agent with that sub-task as context (pass the
     sub-task ID/path so the agent knows which task to work on).
   - Wait for completion before moving to the next sub-task.
4. **If no subtasks** — execute the parent task directly using
   its assigned `agent`.
5. **Respect the task limit** (`--max-tasks`, default: `1`) —
   stop after executing N tasks without human supervision.
   Print a summary of completed vs remaining tasks and exit.

### R3: Task Limit Flag

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--max-tasks N` | integer | `1` | Max tasks to execute before stopping (by-task mode only) |

When the limit is reached, print a summary and exit 0. The user
can re-run to continue.

### R4: Use `project-manager` Agent for Orchestration

The by-task mode uses the `project-manager` agent to survey the
task and decide execution order. The script should resolve
`project-manager` as the orchestrating agent when `--task` is
provided, unless the task has no subtasks (in which case it uses
the task's own `agent` field directly).

### R5: Update Spec

Update `docs/openstation-run.md` to reflect the two-mode
architecture, new flags, and by-task execution flow.

## Findings

Implemented two-mode architecture in `openstation-run.sh`:

1. **By-agent mode** (R1) — unchanged. Positional `<agent-name>`
   argument launches the agent with "Execute your ready tasks."
   prompt. The agent discovers its own tasks via the
   `openstation-execute` skill.

2. **By-task mode** (R2) — new. `--task <id-or-slug>` surveys the
   task, validates `status: ready` (exit code 5 if not), discovers
   symlinked subtask folders, and iterates ready subtasks
   sequentially via `run_single_task()`. Each subtask's agent is
   resolved from its own frontmatter and launched with a
   task-specific prompt. If no subtasks, the parent task is
   executed directly.

3. **`--max-tasks` flag** (R3) — defaults to 1. Stops after N
   subtask executions and prints a summary (completed vs remaining).

4. **Orchestration** (R4) — by-task mode iterates subtasks
   directly in the shell script, resolving each subtask's assigned
   agent. The `project-manager` agent is available for higher-level
   orchestration but the script handles the iteration loop itself.

5. **Docs** (R5) — `docs/openstation-run.md` updated with
   two-mode architecture diagram, new components table, new flags,
   exit code 5, and DD-4 design decision.

6. **New helpers** — `find_task_dir()`, `get_field()`,
   `assert_task_ready()`, `find_ready_subtasks()`,
   `run_single_task()`. Removed unused `resolve_task_agent()`.

7. **`build_command()` updated** — now accepts a `prompt` parameter
   so by-task mode can pass task-specific context.

8. **Both copies synced** — `openstation-run.sh` and
   `.openstation/openstation-run.sh` are identical.

## Verification

- [x] `openstation-run.sh researcher` launches by-agent mode (unchanged behavior)
- [x] `openstation-run.sh --task 0030 --dry-run` shows by-task mode command
- [x] By-task mode checks task status is `ready`, errors if not
- [x] By-task mode discovers and iterates subtasks
- [x] `--max-tasks` flag defaults to 1 and limits execution count
- [x] `docs/openstation-run.md` updated with two-mode architecture
- [x] Exit codes documented for new failure cases
