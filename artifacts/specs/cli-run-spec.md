---
kind: spec
name: cli-run-spec
task: 0038-cli-run-spec
created: 2026-03-03
status: complete
---

# CLI `run` Subcommand

Add an `openstation run` subcommand to `bin/openstation` that
replaces direct invocation of `openstation-run.sh`.

## Problem

Launching agents currently requires calling `openstation-run.sh`
directly — a separate shell script outside the CLI. This creates
two entry points (`bin/openstation` for read-only queries,
`openstation-run.sh` for execution) with inconsistent interfaces.
A unified `openstation run` subcommand brings agent launching
under the same CLI, reusing shared utilities (root detection,
frontmatter parsing, task resolution).

## Architecture

```
openstation run <agent> [OPTIONS]
openstation run --task <id-or-slug> [OPTIONS]
│
├─ parse args ──► mode (by-agent | by-task)
│
├─ find_root()               ← existing (shared with list/show)
│
├─ BY-AGENT path
│   ├─ find_agent_spec()     ← new
│   ├─ parse_allowed_tools() ← new
│   ├─ build_command()       ← new
│   └─ exec_claude()         ← os.execvp (replaces process)
│
├─ BY-TASK path
│   ├─ resolve_task()        ← existing (shared with show)
│   ├─ assert_task_ready()   ← new
│   ├─ find_ready_subtasks() ← new
│   ├─ for each subtask (up to --max-tasks):
│   │   ├─ resolve agent from task frontmatter
│   │   ├─ find_agent_spec()
│   │   ├─ parse_allowed_tools()
│   │   ├─ build_command()
│   │   └─ subprocess.run()  ← subshell (loop continues)
│   └─ print summary
│
└─ --dry-run: print command instead of executing
```

### Data Flow

```
agent spec (agents/*.md)
        │
        ▼
  parse_frontmatter()       ─► dict with allowed-tools (list)
        │
        ▼
  parse_allowed_tools()     ─► ["Read", "Glob", "Bash(ls *)"]
        │
        ▼
  build_command()           ─► ["claude", "-p", "--agent", ...]
        │
        ▼
  os.execvp / subprocess    ─► claude process
```

---

## CLI Interface

```
openstation run <agent-name> [OPTIONS]
openstation run --task <id-or-slug> [OPTIONS]
```

### Positional Argument

| Argument | Description |
|----------|-------------|
| `agent-name` | Agent to launch (by-agent mode). Mutually exclusive with `--task`. |

### Options

| Flag | Type | Default | Shell equivalent | Description |
|------|------|---------|-----------------|-------------|
| `--task` | string | — | `--task` | Task ID or slug (by-task mode). Mutually exclusive with positional agent. |
| `--tier` | int | `2` | `--tier` | Execution tier: 1 (interactive) or 2 (autonomous). |
| `--budget` | float | `5` | `--budget` | Max USD spend per agent invocation (tier 2 only). |
| `--turns` | int | `50` | `--turns` | Max agentic turns per invocation (tier 2 only). |
| `--max-tasks` | int | `1` | `--max-tasks` | Max subtasks to execute before stopping (by-task mode only). |
| `--force` | flag | `false` | `--force` | Skip task status checks (execute regardless of status). |
| `--dry-run` | flag | `false` | `--dry-run` | Print command(s) without executing. |

Every flag from `openstation-run.sh` has a 1:1 equivalent. No
flags are added or removed.

### Mutual Exclusion

Exactly one of `<agent-name>` (positional) or `--task` must be
provided. If both or neither are given, exit with usage error.

---

## Execution Model

### Decision: `os.execvp` for by-agent, `subprocess.run` for by-task

**By-agent mode** launches a single agent and never returns.
Use `os.execvp()` to replace the Python process with `claude`.
This matches the shell script's `exec` behavior and gives clean
signal propagation (Ctrl-C goes directly to `claude`, no zombie
parent).

**By-task mode** iterates a queue of subtasks, launching one
agent per subtask. Use `subprocess.run()` for each invocation
so the Python process survives to continue the loop, print
summaries, and enforce `--max-tasks`.

| Mode | Mechanism | Rationale |
|------|-----------|-----------|
| by-agent | `os.execvp()` | Single launch, clean signals, no post-exec work |
| by-task (single/no subtasks) | `os.execvp()` | Same as by-agent — only one launch needed |
| by-task (multiple subtasks) | `subprocess.run()` per subtask | Must survive to iterate queue and print summary |

### Tier Selection

Tier determines how the `claude` command is constructed:

**Tier 1 (interactive):**
```
claude --agent <name> --permission-mode acceptEdits
```

**Tier 2 (autonomous):**
```
claude -p "<prompt>" \
  --agent <name> \
  --allowedTools <tool1> <tool2> ... \
  --max-budget-usd <N> \
  --max-turns <N> \
  --output-format json
```

### Streaming Output

- **Tier 1**: Claude runs interactively — stdout/stderr pass
  through directly (inherited file descriptors via `execvp`
  or `subprocess.run` without `capture_output`).
- **Tier 2**: Claude runs in print mode with `--output-format json`.
  Output goes to stdout. The `run` subcommand does not parse or
  transform the output — it passes through verbatim.

### Prompt Construction

- **By-agent**: `"Execute your ready tasks."` (agent discovers
  tasks via the `openstation-execute` skill).
- **By-task**: `"Execute task <name>. Read its spec at
  artifacts/tasks/<name>/index.md and work through the
  requirements."` (explicit task reference).

---

## Agent Resolution

### `find_agent_spec(root, prefix, agent_name)`

Locates the agent's markdown spec file. Checks paths in order:

1. `{root}/{prefix}/agents/{agent_name}.md` (installed path,
   when prefix is `.openstation`)
2. `{root}/agents/{agent_name}.md` (source repo path)

Returns the `Path` object. Raises/exits if not found.

This mirrors the shell script's `find_agent_spec()` but is
implemented in Python using `pathlib`.

### Task-to-Agent Resolution

In by-task mode, the agent is read from the task's frontmatter
`assignee` field using the existing `parse_frontmatter()` function.
If the field is missing or empty, exit with an error.

---

## Allowed-Tools Parsing

### `parse_allowed_tools(spec_path)`

Reads the `allowed-tools` YAML list from an agent spec file.
Returns a list of tool strings.

**Algorithm:**

1. Read the file line by line.
2. Find the `allowed-tools:` key.
3. Collect subsequent lines matching `^\s*-\s+(.+)` until
   the next non-list line or end-of-frontmatter (`---`).
4. For each list item, strip leading `- `, then strip
   surrounding quotes (single or double).

**Examples:**

```yaml
allowed-tools:
  - Read
  - Glob
  - "Bash(ls *)"
```

Yields: `["Read", "Glob", "Bash(ls *)"]`

**Why not reuse `parse_frontmatter()`?**

The existing `parse_frontmatter()` in `bin/openstation` handles
flat `key: value` pairs via `str.partition(':')`. It does not
handle YAML list fields. Rather than replacing it with a full
YAML parser (adding a dependency), `parse_allowed_tools()` is
a dedicated parser for this one list field. If more list fields
are needed later, consider switching to PyYAML.

### Passing to Claude

Each tool string becomes a separate `--allowedTools` argument:

```
--allowedTools Read Glob Grep "Bash(ls *)"
```

The list is passed as `*tools` expansion in the command array.
No shell escaping needed since `subprocess`/`execvp` use arrays.

---

## Error Handling

### Exit Codes

| Code | Name | When |
|------|------|------|
| 0 | Success | Command completed |
| 1 | Usage error | Bad args, missing agent in task, missing allowed-tools, both agent and --task given, neither given |
| 2 | Agent not found | Agent spec file does not exist at expected paths |
| 3 | Claude not found | `claude` not on `$PATH` |
| 4 | Agent error | `claude` process exited non-zero |
| 5 | Task not ready | Task status is not `ready` (bypassed with `--force`) |

These match `openstation-run.sh` exit codes exactly.

### Error Scenarios

| Scenario | Behavior |
|----------|----------|
| `claude` not installed | Check `shutil.which("claude")` before any work. Print `error: claude CLI not found on $PATH`, exit 3. |
| Agent spec not found | After `find_agent_spec()` fails. Print `error: Agent spec not found: <name>`, exit 2. |
| No `allowed-tools` in spec | After parsing yields empty list. Print `error: No allowed-tools found in agent spec: <path>`, exit 1. |
| Task not found | Reuse `resolve_task()` from existing CLI. Print `error: task not found: <ref>`, exit 1. |
| Task not ready | Check `status` field. Print `error: Task <name> has status '<status>' (expected 'ready')`, exit 5. Bypassed with `--force`. |
| No agent in task | Task's `assignee` field empty/missing. Print `error: No agent assigned to task: <name>`, exit 1. |
| Both agent and --task | Arg parse validation. Print `error: Specify either an agent name or --task, not both`, exit 1. |
| Neither agent nor --task | Arg parse validation. argparse handles this via `required=True` on subparser or manual check. |
| Invalid tier | `choices=[1, 2]` in argparse. Print usage error automatically. |
| Agent exits non-zero | By-task mode: capture return code, print `error: Subtask <name> failed`, break loop. By-agent mode: exit code propagates via `execvp`. |

### Error Format

All errors print `error: <message>` to stderr via the existing
`err()` helper. No stack traces. Consistent with `list`/`show`.

---

## Integration with Existing CLI

### Subcommand Registration

Add `run` alongside `list` and `show` in `main()`:

```python
run_p = sub.add_parser("run", help="Launch an agent")
run_p.add_argument("agent", nargs="?", default=None,
                   help="Agent name (by-agent mode)")
run_p.add_argument("--task", default=None,
                   help="Task ID or slug (by-task mode)")
run_p.add_argument("--tier", type=int, default=2, choices=[1, 2],
                   help="Execution tier (default: 2)")
run_p.add_argument("--budget", type=float, default=5,
                   help="Max USD per invocation (tier 2)")
run_p.add_argument("--turns", type=int, default=50,
                   help="Max turns per invocation (tier 2)")
run_p.add_argument("--max-tasks", type=int, default=1,
                   help="Max subtasks to execute (by-task)")
run_p.add_argument("--force", action="store_true",
                   help="Skip status checks")
run_p.add_argument("--dry-run", action="store_true",
                   help="Print command without executing")
```

### Shared Code

Functions reused from existing CLI:

| Function | Used by |
|----------|---------|
| `find_root()` | `list`, `show`, `run` |
| `parse_frontmatter()` | `list`, `show`, `run` |
| `resolve_task()` | `show`, `run` (by-task mode) |
| `err()` | all commands |

New functions added:

| Function | Purpose |
|----------|---------|
| `find_agent_spec(root, prefix, name)` | Locate agent `.md` file |
| `parse_allowed_tools(spec_path)` | Extract tool list from frontmatter |
| `build_command(agent, tier, budget, turns, prompt, tools)` | Assemble `claude` argv |
| `assert_task_ready(spec_path)` | Validate task status |
| `find_ready_subtasks(task_dir, force)` | Scan for ready subtask symlinks |
| `run_single_task(root, prefix, task_dir, tier, budget, turns, dry_run)` | Execute one task |
| `cmd_run(args, root, prefix)` | Top-level run handler |

### Single-File Constraint

All new code goes into `bin/openstation`. The single-file pattern
(DD-1 from `cli-feature-spec.md`) is preserved. The file grows
from ~230 lines to ~400 lines — still manageable in a single file.

### CLI Description Update

The parser description changes from "Read-only CLI for the
Open Station task vault" to "CLI for the Open Station task vault"
since `run` introduces a non-read-only command.

---

## Components

| # | Component | Location | Purpose |
|---|-----------|----------|---------|
| C1 | Run subcommand | `bin/openstation` (in `cmd_run`) | Top-level handler, mode dispatch |
| C2 | Agent resolver | `bin/openstation` (in `find_agent_spec`) | Locate agent spec by name |
| C3 | Tools parser | `bin/openstation` (in `parse_allowed_tools`) | Extract allowed-tools list from frontmatter |
| C4 | Command builder | `bin/openstation` (in `build_command`) | Assemble claude argv for tier 1/2 |
| C5 | Task executor | `bin/openstation` (in `run_single_task`) | Resolve agent, build command, launch for one task |
| C6 | Subtask scanner | `bin/openstation` (in `find_ready_subtasks`) | Find symlinked ready subtasks |
| C7 | Integration tests | `tests/test_cli.py` | Test run command with mocked claude |

---

## Testing Strategy

### Approach: Mock `claude` with a No-Op Script

Tests cannot invoke the real `claude` CLI. Instead:

1. Create a mock `claude` script in the temp directory that
   prints its arguments as JSON and exits 0.
2. Prepend the temp directory to `PATH` so the mock is found
   first.
3. Use `--dry-run` for most tests (no subprocess needed).
4. For execution tests, verify the mock received correct args.

### Test Categories

**Dry-run output (no subprocess):**
- By-agent tier 1 prints correct command
- By-agent tier 2 prints command with `--allowedTools`, `--max-budget-usd`, `--max-turns`
- By-task prints command with task-specific prompt
- Custom `--budget`, `--turns` values appear in output

**Argument validation:**
- Both agent and `--task` → exit 1
- Neither agent nor `--task` → exit 1 (or usage)
- Invalid `--tier` → exit 1
- Missing agent spec → exit 2
- Missing allowed-tools → exit 1

**Task resolution (by-task mode):**
- Task found by ID prefix
- Task found by full slug
- Task not found → exit 1
- Task not ready → exit 5
- Task not ready + `--force` → proceeds

**Subtask discovery:**
- No subtasks → runs parent task
- Ready subtasks → runs subtasks
- `--max-tasks` limits execution count

**Error handling:**
- Claude not on PATH → exit 3
- Agent exits non-zero → exit 4 (captured in by-task mode)

---

## Design Decisions

### DD-1: `os.execvp` for by-agent mode

Python replaces itself with `claude` — no parent process stays
alive. Signals (SIGINT, SIGTERM) go directly to `claude`. Matches
the shell script's `exec` behavior.

**Trade-off:** No post-execution cleanup possible. Acceptable
because there's nothing to clean up in by-agent mode.

### DD-2: Dedicated `parse_allowed_tools` instead of extending `parse_frontmatter`

The existing frontmatter parser handles flat `key: value` pairs.
YAML list parsing is a different concern (indented `- item` lines).
A dedicated function keeps the flat parser simple and avoids
introducing a YAML dependency.

**Trade-off:** Two parsing paths for the same file. Acceptable
because the list format is stable and small.

### DD-3: Single file preserved

Adding ~170 lines to `bin/openstation` keeps the single-file
pattern. The alternative (splitting into a package) adds import
paths, `__init__.py`, and install complexity for marginal benefit
at this scale.

**Revisit when:** The file exceeds ~600 lines or needs a third
non-trivial subcommand.

### DD-4: Constants match shell script

Default values (`TIER=2`, `BUDGET=5`, `TURNS=50`, `MAX_TASKS=1`)
and exit codes match `openstation-run.sh` exactly. This ensures
`openstation run` is a drop-in replacement.

### DD-5: No output parsing or transformation

The `run` command does not parse `claude`'s stdout/stderr. It
passes through file descriptors directly. This avoids coupling
to Claude's output format and keeps the implementation simple.

---

## Migration

Once `openstation run` is implemented and tested:

1. Update `/openstation.dispatch` to reference `openstation run`
   instead of `openstation-run.sh`.
2. Keep `openstation-run.sh` as a deprecated shim that calls
   `openstation run` with the same arguments, for backward
   compatibility.
3. Remove the shim after one release cycle.

---

## Verification

| Criterion | How to verify |
|-----------|--------------|
| All shell flags have CLI equivalents | Compare tables above — 1:1 mapping confirmed |
| Execution model justified | DD-1: `execvp` for single launch, `subprocess.run` for queue |
| Agent resolution defined | `find_agent_spec()` checks installed then source paths |
| Task resolution defined | Reuses `resolve_task()` + new `assert_task_ready()` + `find_ready_subtasks()` |
| Allowed-tools parsing defined | `parse_allowed_tools()` algorithm and examples documented |
| Error cases enumerated | Exit codes table + error scenarios table cover all paths |
| Integration with CLI defined | Subcommand registration, shared functions, single-file constraint |
