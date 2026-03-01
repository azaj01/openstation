---
kind: spec
name: openstation-run
---

# openstation-run.sh

Shell launcher for Open Station agents. Wraps the `claude` CLI
with tier-based execution modes, agent resolution, and tool
sandboxing.

## Purpose

Agents need a controlled launch mechanism that collects runnable
tasks and executes them under sandboxed, tiered constraints.
The script is the single entry point for all agent execution,
organized as a two-stage pipeline:

1. **Task collection** — determine what to run (agent
   self-discovery or script-driven task survey)
2. **Task execution** — launch agents under tier-based
   constraints with tool sandboxing and budget caps

## Task Collection

How the runnable task set is determined. The CLI argument selects
one of two collection strategies:

| Strategy | CLI | Collector | Result |
|----------|-----|-----------|--------|
| By agent | `<agent-name>` | Agent self-discovers at runtime via `openstation-execute` skill | Agent-managed (opaque to script) |
| By task | `--task <ref>` | Script surveys task tree: reads `index.md`, finds ready subtasks, or falls back to parent | Ordered list of `(task-dir, agent-name)` pairs |

### Agent Collection

```
openstation-run.sh <agent-name> [OPTIONS]
```

The script doesn't know or manage which tasks run — the agent
handles discovery internally via the `openstation-execute` skill.
The script's job is just to resolve the agent spec, parse tools,
and launch.

### Task Collection

```
openstation-run.sh --task <id-or-slug> [OPTIONS]
```

The script builds an explicit task queue:

1. **Survey** — finds the task folder, reads `index.md`, validates
   `status: ready` (exits with code 5 if not).
2. **Discover subtasks** — scans for symlinked sub-task folders
   inside the task directory. Filters to `status: ready`.
3. **If subtasks exist** — queues ready subtasks sequentially,
   resolving each subtask's `agent` field into an ordered list
   of `(task-dir, agent-name)` pairs.
4. **If no subtasks** — queues the parent task directly using
   its assigned `agent`.

`--max-tasks` (default: 1) caps how many queued tasks are
consumed per invocation.

## Task Execution

How each collected task is executed. Always by an agent, always
through the `claude` CLI. The execution machinery is shared
regardless of which collection strategy produced the task set.

### Components

- **Agent resolution** — `find_agent_spec()` locates the agent's
  `.md` spec (installed path first, source repo fallback)
- **Tool sandboxing** — `parse_allowed_tools()` extracts the
  allowlist from the agent spec's `allowed-tools` YAML field
- **Command assembly** — `build_command()` builds the `claude`
  invocation array (no string eval, pure bash arrays)
- **Tier enforcement** — tier 1 (interactive: `acceptEdits`
  permission) vs tier 2 (autonomous: explicit tools, budget, turns)
- **Process lifecycle** — agent collection uses `exec` (replaces
  shell), task collection uses subshells (iterates queue)

## File Locations

| Copy | Path | Consumers |
|------|------|-----------|
| Source repo | `openstation-run.sh` | Developers working on Open Station itself |
| Installed | `.openstation/openstation-run.sh` | Target projects after `install.sh` |

Both copies are identical. `install.sh` is responsible for syncing.

## Architecture

```
CLI invocation
│
├─ parse args ──► agent name OR --task reference
│
├─ find_project_root()
│   └─ walk up from CWD
│       ├─ .openstation/ dir → installed project
│       └─ agents/ + install.sh → source repo
│
│
│  ┌─────────── COLLECTION ───────────┐
│  │                                   │
├─ AGENT collection (positional arg)   │
│   └─ (opaque — agent discovers       │
│       tasks at runtime)              │
│                                      │
├─ TASK collection (--task flag)       │
│   ├─ find_task_dir() → canonical     │
│   ├─ assert_task_ready() → exit 5    │
│   ├─ find_ready_subtasks()           │
│   │   └─ scan symlinks, filter ready │
│   ├─ IF subtasks → queue each        │
│   └─ IF none → queue parent          │
│                                      │
│  └──────────────────────────────────┘
│
│
│  ┌─────────── EXECUTION ────────────┐
│  │                                   │
├─ find_agent_spec()                   │
│   ├─ .openstation/agents/<name>.md   │
│   └─ agents/<name>.md (fallback)     │
│                                      │
├─ parse_allowed_tools()               │
│   └─ read allowed-tools: YAML list   │
│                                      │
├─ build_command()                     │
│   ├─ tier 1 → claude --agent <name>  │
│   │           --permission-mode      │
│   │           acceptEdits            │
│   └─ tier 2 → claude -p <prompt>     │
│               --agent <name>         │
│               --allowedTools ...     │
│                                      │
├─ AGENT → exec (replaces shell)       │
├─ TASK  → subshell per queued task    │
│                                      │
│  └──────────────────────────────────┘
```

## Execution Tiers

| Tier | Mode | Permission | Prompt | Output | Use Case |
|------|------|------------|--------|--------|----------|
| 1 | Interactive | `acceptEdits` | None (user types) | Normal | Human-supervised agent work |
| 2 | Autonomous | Explicit `--allowedTools` | `"Execute your ready tasks."` | JSON | Unattended batch execution |

**Tier 2 is the default.** Tier 1 is opt-in via `--tier 1`.

### Tier 2 Constraints

| Constraint | Default | Flag |
|------------|---------|------|
| Budget | $5 USD | `--budget N` |
| Turns | 50 | `--turns N` |
| Tools | From agent spec `allowed-tools` | — |

These constraints are ignored for tier 1 (interactive mode
handles its own permissions).

## CLI Interface

```
openstation-run.sh <agent-name> [OPTIONS]
openstation-run.sh --task <id-or-slug> [OPTIONS]
```

### Options

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--task ID` | string | — | Execute task by ID or slug (by-task mode) |
| `--max-tasks N` | integer | `1` | Max tasks to execute before stopping (by-task mode only) |
| `--tier 1\|2` | integer | `2` | Execution tier |
| `--budget N` | integer | `5` | Max spend in USD per agent invocation (tier 2 only) |
| `--turns N` | integer | `50` | Max agentic turns per agent invocation (tier 2 only) |
| `--dry-run` | flag | off | Print command(s) without executing |
| `--help` | flag | — | Show usage |

### Mode Selection

Exactly one of `<agent-name>` or `--task` must be provided.

- **By-agent**: `openstation-run.sh researcher` — launches the
  `researcher` agent to find and execute its own ready tasks.
- **By-task**: `openstation-run.sh --task 0013` — finds the task
  folder matching `0013*` in `artifacts/tasks/`, validates its
  status is `ready`, discovers subtasks, and executes them.

### Exit Codes

| Code | Constant | Meaning |
|------|----------|---------|
| 0 | — | Success |
| 1 | `EXIT_USAGE` | Bad arguments, missing tools, no agent in task |
| 2 | `EXIT_NO_AGENT` | Agent spec file not found |
| 3 | `EXIT_NO_CLAUDE` | `claude` CLI not on `$PATH` |
| 4 | `EXIT_AGENT_ERROR` | Agent process exited with error |
| 5 | `EXIT_TASK_NOT_READY` | Task status is not `ready` (by-task mode) |

## Components

### Execution Helpers

| Component | Purpose |
|-----------|---------|
| `find_project_root()` | Walk up from CWD to find project root |
| `find_agent_spec()` | Locate agent `.md` file (installed or source) |
| `parse_allowed_tools()` | Extract tool allowlist from agent spec YAML |
| `build_command()` | Assemble `claude` CLI invocation array |
| `get_field()` | Read a single YAML frontmatter field from a spec file |

### Collection Helpers (task collection only)

| Component | Purpose |
|-----------|---------|
| `find_task_dir()` | Find canonical task directory by ID or slug |
| `assert_task_ready()` | Validate task status is `ready` |
| `find_ready_subtasks()` | Scan task dir for symlinked sub-tasks with `ready` status |
| `run_single_task()` | Launch an agent for one task (resolve agent, build cmd, exec) |

### find_project_root

Walks up the directory tree from `$PWD`. Two detection patterns:

1. `.openstation/` directory → installed project (takes precedence)
2. `agents/` dir + `install.sh` file → source repo

Returns the directory path via stdout. Returns exit code 1 if
neither pattern is found.

### parse_allowed_tools

Reads the `allowed-tools:` YAML list from an agent spec's
frontmatter. Handles bare values (`- Read`) and quoted values
(`- "Bash(ls *)"` or `- 'Bash(ls *)'`). Outputs one tool per
line to stdout.

Stops parsing when it hits either:
- End of frontmatter (`---`)
- A non-list-item line (start of next YAML key)

### find_agent_spec

Checks two paths in order:
1. `.openstation/agents/<name>.md` (installed)
2. `agents/<name>.md` (source)

Returns the first existing path. Exits with `EXIT_NO_AGENT` if
neither exists.

### build_command

Builds a bash array (`CMD`) — no string eval. Accepts a prompt
parameter so callers can provide context-specific prompts. Tier
determines the shape:

- **Tier 1**: `claude --agent <name> --permission-mode acceptEdits`
- **Tier 2**: `claude -p "<prompt>" --agent <name> --allowedTools <tools> --max-budget-usd N --max-turns N --output-format json`

### find_task_dir

Scans `artifacts/tasks/*/` for a folder matching the given
reference (numeric ID `0013` or full slug `0013-my-task`).
Returns the canonical directory path. Exits with `EXIT_USAGE`
if not found.

### assert_task_ready

Reads a task's `index.md` and checks that `status` is `ready`.
Exits with `EXIT_TASK_NOT_READY` (code 5) if the status is
anything else.

### find_ready_subtasks

Scans a task directory for symlinked sub-task folders. For each
symlinked entry that contains an `index.md`, reads the `status`
field. Prints paths of sub-tasks with `status: ready`, one per
line.

### run_single_task

Self-contained task executor used in by-task mode. For a given
task directory:

1. Reads the `agent` field from the task's frontmatter
2. Locates the agent spec and parses allowed tools
3. Builds a `claude` command with a task-specific prompt
4. Executes in a subshell (not `exec`, so the loop can continue)

Returns the agent process exit code.

## Dependencies

| Dependency | Required | Purpose |
|------------|----------|---------|
| `claude` CLI | yes | Agent runtime |
| `bash` 4+ | yes | `mapfile`, arrays |
| `sed` | yes | Frontmatter field extraction |
| Agent spec with `allowed-tools` | yes | Tool sandboxing |

## Design Decisions

### DD-1: Shell script, not Python

The run script stays as bash because it is a thin wrapper
around `claude` CLI invocation. There is no parsing complexity
that benefits from Python — the heavy lifting is argument
assembly and `exec`. The Python CLI (`bin/openstation`) handles
read-only operations (`list`, `show`) where structured output
matters.

### DD-2: exec replaces the shell process

The script uses `exec "${CMD[@]}"` rather than running claude
as a child process. This means the agent process inherits the
script's PID, signal handling works naturally, and there is no
zombie process risk.

### DD-3: Allowed-tools are mandatory

If no `allowed-tools` are found in the agent spec, the script
exits with an error rather than falling back to unrestricted
access. This is a safety guardrail — agents must declare their
tool surface.

### DD-4: Collection and execution are orthogonal

Previously, `--task` simply resolved a task to its agent name
and then launched identically to by-agent mode. This conflated
how tasks are *collected* with how they are *executed*. The spec
now separates these into two pipeline stages:

- **Collection** — determines the task set (agent self-discovery
  vs script-driven survey). Two strategies, selected by CLI arg.
- **Execution** — launches agents under tier constraints. Shared
  machinery regardless of collection strategy.

The only execution difference is process lifecycle: agent
collection uses `exec` (replaces shell), task collection uses
subshells so the script can iterate and print a summary.
`--max-tasks` (default: 1) caps consumption per invocation.

### DD-5: Project root detection precedence

`.openstation/` is checked before `agents/ + install.sh` so
that installed projects take precedence over the source repo
when both patterns exist (e.g., when developing Open Station
with itself installed).
