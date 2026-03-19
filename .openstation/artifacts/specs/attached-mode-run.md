---
kind: spec
name: attached-mode-run
task: 0119-research-attached-mode-for-openstation
created: 2026-03-12
status: implemented
---

# Attached Mode for `openstation run`

Add `--attached` / `-a` flag to `openstation run` that launches an
interactive Claude session with task context pre-loaded, replacing
the current `--tier` flag and the `agents dispatch` subcommand.

## Problem

`openstation run` currently operates in detached mode only — the
agent runs autonomously via `-p` (non-interactive) with stream-json
capture. Users who want to participate in a task session must use
`--tier 1`, which launches a bare interactive session **without**
the task prompt or tool restrictions. The `agents dispatch` command
has the same limitation. There is no way to get an interactive
session that includes the task context.

## Decisions

| Decision | Status | Rationale |
|----------|--------|-----------|
| Add `--attached` / `-a` flag | **Decided** | Clear metaphor (vs detached default), no `-a` conflicts in current CLI |
| Remove `--tier` flag entirely | **Decided** | Young project, no external users; `--attached` is a strict superset of tier 1, tier 2 is the default |
| Remove `agents dispatch` subcommand | **Decided** | `openstation run <agent> --attached` covers the same use case with tool restrictions; see task 0120 |
| Single-task only in attached mode | **Decided** | Interactive sessions use `os.execvp`; cannot loop through N interactive sessions |
| No log capture in attached mode | **Decided** | Claude persists sessions internally; `--resume` provides replay |
| Prompt as positional argument | **Decided** | `claude --agent <name> "prompt"` starts interactive REPL with prompt as first message |

## Architecture

```
openstation run --task 0042 --attached
│
├─ parse args
│   ├─ validate: --attached incompatible with --json, --quiet
│   └─ warn: --budget, --turns ignored in attached mode
│
├─ resolve task (existing logic, unchanged)
│
├─ check for subtasks
│   └─ if subtasks found → ERROR (attached = single-task only)
│
├─ resolve agent + tools (existing logic, unchanged)
│
├─ build_command(attached=True)
│   └─ ["claude", "--agent", <name>, "--allowedTools", ...tools, <prompt>]
│
└─ os.execvp (replace process)
```

### By-agent mode with `--attached`

```
openstation run researcher --attached
│
├─ resolve agent spec (existing logic)
├─ parse allowed-tools (existing logic)
├─ build_command: ["claude", "--agent", "researcher", "--allowedTools", ...tools]
│   └─ no task prompt (same as current by-agent behavior, but with tools)
└─ os.execvp
```

## CLI Interface

### New flag

```
--attached, -a    Launch interactive session (replaces process via execvp)
```

### Removed flags

```
--tier {1,2}      Remove entirely. Tier 2 behavior becomes the unnamed default.
                  Tier 1 is replaced by --attached.
```

### Updated help text

```
openstation run <agent> [OPTIONS]       Launch agent (detached by default)
openstation run --task <id> [OPTIONS]   Execute a specific task

options:
  --attached, -a       Interactive mode (replace process, no log capture)
  --budget USD         Max USD per invocation (detached only, default: 5)
  --turns N            Max turns per invocation (detached only, default: 50)
  --max-tasks N        Max subtasks to execute (detached only, default: 1)
  --force              Skip task status checks
  --dry-run            Print command without executing
  -q, --quiet          Suppress progress output (detached only)
  -j, --json           Structured JSON dry-run output (detached only)

examples:
  openstation run researcher --attached       # interactive agent session
  openstation run --task 0042 --attached      # interactive task session
  openstation run --task 0042                 # autonomous (detached)
  openstation run --task 0042 --attached --dry-run  # preview attached command
```

### Incompatibility enforcement

| Combination | Behavior |
|-------------|----------|
| `--attached` + `--json` | Error: "JSON output not supported in attached mode" |
| `--attached` + `--quiet` | Error: "Quiet mode not supported in attached mode" |
| `--attached` + `--budget` | Warning to stderr, then proceed (flag ignored) |
| `--attached` + `--turns` | Warning to stderr, then proceed (flag ignored) |
| `--attached` + `--max-tasks` | Warning to stderr, then proceed (flag ignored) |
| `--attached` + `--dry-run` | Allowed — prints the command that would be `execvp`'d |
| `--attached` + task with ready subtasks | Error: "Attached mode requires a single task. This task has N ready subtasks. Use --task <subtask-id> to target one." |

## Code Changes

### `src/openstation/cli.py`

1. **Remove** `--tier` argument from `run_p`
2. **Add** `--attached` / `-a` as `store_true`
3. **Update** help strings for `--budget`, `--turns` to say "detached only"
4. **Update** examples in epilog
5. **Remove** `agents dispatch` subparser entirely

### `src/openstation/run.py`

#### Remove `DEFAULT_TIER`

```python
# Delete
DEFAULT_TIER = 2
```

#### Modify `build_command` signature

```python
# Before
def build_command(agent_name, tier, budget, turns, prompt, tools, output_format="json"):

# After
def build_command(agent_name, budget, turns, prompt, tools,
                  output_format="json", attached=False):
```

#### `build_command` — attached branch

```python
def build_command(agent_name, budget, turns, prompt, tools,
                  output_format="json", attached=False):
    if attached:
        cmd = ["claude", "--agent", agent_name, "--allowedTools"]
        cmd.extend(tools)
        if prompt:
            cmd.append(prompt)       # positional — interactive REPL
        return cmd

    # Detached (current tier-2 logic, minus the tier parameter)
    cmd = [
        "claude",
        "-p", prompt,
        "--agent", agent_name,
        "--allowedTools",
    ]
    cmd.extend(tools)
    cmd.extend([
        "--max-budget-usd", str(budget),
        "--max-turns", str(turns),
        "--output-format", output_format,
    ])
    if output_format == "stream-json":
        cmd.append("--verbose")
    return cmd
```

#### `cmd_run` — attached validation

Add after argument extraction (around line 422):

```python
attached = args.attached

if attached:
    if getattr(args, "json", False):
        core.err("JSON output not supported in attached mode")
        return core.EXIT_USAGE
    if getattr(args, "quiet", False):
        core.err("Quiet mode not supported in attached mode")
        return core.EXIT_USAGE
    if args.budget != DEFAULT_BUDGET:
        core.warn("--budget is ignored in attached mode")
    if args.turns != DEFAULT_TURNS:
        core.warn("--turns is ignored in attached mode")
```

#### `cmd_run` — attached + subtasks guard

In the by-task path, after `subtasks = tasks.find_ready_subtasks(...)`:

```python
if attached and subtasks:
    core.err(
        f"Attached mode requires a single task. "
        f"This task has {len(subtasks)} ready subtask(s). "
        f"Use --task <subtask-id> to target one."
    )
    return core.EXIT_USAGE
```

#### `cmd_run` — attached execution (by-task, no subtasks)

Replace the `_exec_or_run` call in the no-subtasks branch:

```python
if attached:
    cmd = build_command(agent, budget, turns, prompt, tools, attached=True)
    if dry_run:
        # dry-run logic (same as existing)
        ...
    core.header(f"openstation run --task {task_name} --attached")
    core.detail("Task", task_name)
    core.detail("Agent", agent)
    core.detail("Mode", "attached")
    os.execvp(cmd[0], cmd)
```

#### `cmd_run` — attached execution (by-agent)

In the by-agent path, when `attached` is true:

```python
if attached:
    cmd = build_command(agent_name, budget, turns, prompt, tools, attached=True)
    if dry_run:
        ...
    os.execvp(cmd[0], cmd)
```

#### Remove `cmd_agents_dispatch`

Delete the entire function. It is replaced by
`openstation run <agent> --attached`.

#### Remove tier references

- Delete `tier = args.tier` from `cmd_run`
- Remove `tier` parameter from `run_single_task`, `_exec_or_run`,
  and all call sites
- Remove `core.detail("Tier", str(tier))` logging

### `src/openstation/run.py` — functions to update

| Function | Change |
|----------|--------|
| `build_command` | Replace `tier` param with `attached` param |
| `run_single_task` | Remove `tier` param, always use detached path |
| `_exec_or_run` | Remove `tier` param, always use detached path |
| `cmd_run` | Add attached validation, replace tier with attached |
| `cmd_agents_dispatch` | Delete entirely |

### `commands/openstation.dispatch.md`

Delete this file.

### `docs/cli.md`

Update `run` section: remove `--tier`, add `--attached`. Remove
`agents dispatch` from the agents subcommand table.

### `CLAUDE.md`

Remove `agents dispatch` from the CLI reference table. Add
`--attached` to the `run` examples.

### `tests/test_cli.py`

- Remove any tests for `--tier` flag
- Remove any tests for `agents dispatch`
- Add tests for `--attached` flag:
  - `--attached` + `--json` → error
  - `--attached` + `--quiet` → error
  - `--attached` builds correct command (no `-p`, positional prompt)
  - `--attached` + subtasks → error
  - `--dry-run --attached` prints the interactive command

## Migration

No deprecation period needed — this is a young project with no
external consumers. The change is a single release:

1. Remove `--tier` and `agents dispatch`
2. Add `--attached`
3. Update all docs in the same commit

## Verification

- [x] `openstation run --task 0042 --attached --dry-run` prints
      `claude --agent <name> --allowedTools ... "Execute task ..."`
- [x] `openstation run researcher --attached --dry-run` prints
      `claude --agent researcher --allowedTools ...`
- [x] `--attached` + `--json` → error exit
- [x] `--attached` + `--quiet` → error exit
- [x] `--attached` + task with subtasks → error with hint
- [x] `--tier` flag no longer accepted
- [x] `openstation agents dispatch` no longer accepted
- [x] Detached mode (default) unchanged — budget, turns, stream-json all work
- [x] `commands/openstation.dispatch.md` deleted
- [x] No remaining references to `--tier` or `agents dispatch` in docs
