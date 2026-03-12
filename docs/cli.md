---
kind: spec
name: cli-reference
---

# CLI Reference

## Quick Reference

| Command   | Description                                  |
|-----------|----------------------------------------------|
| `list`    | List tasks (default: active tasks)           |
| `show`    | Display a single task spec                   |
| `create`  | Create a new task                            |
| `status`  | Change a task's lifecycle status             |
| `run`     | Launch an agent on tasks                     |
| `agents`  | Manage and inspect agent specs               |
| `init`    | Initialize Open Station in current directory |

## Global Flags

| Flag        | Description              |
|-------------|--------------------------|
| `--version` | Print version and exit   |
| `--help`    | Show help for any command |

---

## `list`

List tasks from the vault.

### Synopsis

```
openstation list [FILTER] [--status STATUS] [--assignee NAME]
                 [--type TYPE] [-q | -j | -v]
```

### Arguments

| Argument | Description |
|----------|-------------|
| `FILTER` | Optional. Task ID/slug or assignee name (auto-detected). Numeric values resolve as task IDs and show the subtask tree; non-numeric values filter by assignee. |

### Flags

| Flag               | Default  | Description |
|--------------------|----------|-------------|
| `--status STATUS`  | `active` | Filter by status: `backlog`, `ready`, `in-progress`, `review`, `done`, `failed`, `active`, or `all`. `active` = ready + in-progress + review. When a task ID is given as FILTER, defaults to `all`. |
| `--assignee NAME`  | —        | Filter by assignee (exact match) |
| `--type TYPE`      | —        | Filter by type: `feature`, `research`, `spec`, `implementation`, `documentation` |
| `-q`, `--quiet`    | —        | One task name per line, no header (pipe-friendly) |
| `-j`, `--json`     | —        | JSON array of task objects |
| `-v`, `--vim`      | —        | Open matching task files in `$EDITOR` (default: vim) |

Output flags (`-q`, `-j`, `-v`) are mutually exclusive.

### Examples

```bash
openstation list                          # active tasks (ready + in-progress + review)
openstation list --status all             # all tasks regardless of status
openstation list --status ready --assignee researcher
openstation list -q --status ready        # one task name per line
openstation list --json                   # JSON array of task objects
openstation list --vim                    # open active tasks in editor
openstation list 0042                     # show task 0042 and its subtask tree
```

---

## `show`

Display a single task spec.

### Synopsis

```
openstation show TASK [-j | -v]
```

### Arguments

| Argument | Description |
|----------|-------------|
| `TASK`   | Required. Task ID, slug, or full name. Short numeric IDs are zero-padded automatically (e.g. `42` → `0042`). |

### Flags

| Flag            | Description |
|-----------------|-------------|
| `-j`, `--json`  | Emit parsed frontmatter and body as a JSON object |
| `-v`, `--vim`   | Open the task file in `$EDITOR` (default: vim) |

### Task Resolution

Resolution tries these strategies in order (first match wins):

1. **Exact match** — full task name (e.g. `0042-cli-improvements`)
2. **ID prefix** — zero-padded numeric prefix (e.g. `0042` or `42`)
3. **Slug match** — slug portion after the ID (e.g. `cli-improvements`)

Ambiguous matches produce an error listing all candidates.

### Examples

```bash
openstation show 0042                     # show by numeric ID
openstation show 42                       # short ID (auto-padded)
openstation show 0042-cli-improvements    # show by full name
openstation show cli-improvements         # show by slug
openstation show 0042 --json              # frontmatter + body as JSON
openstation show 0042 --vim               # open in editor
```

---

## `create`

Create a new task file in `artifacts/tasks/`.

### Synopsis

```
openstation create DESCRIPTION [--assignee NAME] [--owner NAME]
                   [--status STATUS] [--type TYPE] [--parent TASK]
```

### Arguments

| Argument      | Description |
|---------------|-------------|
| `DESCRIPTION` | Required. Free-text task description. Used to generate the slug (kebab-case, max 5 words) and H1 title. |

### Flags

| Flag              | Default   | Description |
|-------------------|-----------|-------------|
| `--assignee NAME` | —         | Agent name to assign |
| `--owner NAME`    | `user`    | Who verifies: agent name or `user` |
| `--status STATUS` | see below | Initial status: `backlog` or `ready` only |
| `--type TYPE`     | `feature` | Task type: `feature`, `research`, `spec`, `implementation`, `documentation` |
| `--parent TASK`   | —         | Parent task ID/slug. Wikilink added to child's `parent` field and parent's `subtasks` list automatically. |

**Status default logic:** If `--parent` is set and no `--status` given, inherits the parent's status when the parent is `backlog` or `ready`; otherwise defaults to `backlog`. Without `--parent`, defaults to `backlog`.

**Parent auto-promotion:** When creating a sub-task, the parent is auto-promoted through valid transitions if the child's status outranks it.

### Examples

```bash
openstation create "add login page"
openstation create "fix auth bug" --assignee developer --status ready
openstation create "child task" --parent 0042
```

Prints the created task name (e.g. `0113-add-login-page`) to stdout.

---

## `status`

Change a task's lifecycle status.

### Synopsis

```
openstation status TASK NEW_STATUS
```

### Arguments

| Argument     | Description |
|--------------|-------------|
| `TASK`       | Required. Task ID, slug, or full name. |
| `NEW_STATUS` | Required. Target status: `backlog`, `ready`, `in-progress`, `review`, `done`, `failed`. |

### Valid Transitions

```
backlog → ready → in-progress → review → done
                   ready → backlog
                                  review → failed → in-progress
```

Invalid transitions produce an error showing allowed targets from the current status.

If the task has a parent, auto-promotion is applied after a successful transition.

### Examples

```bash
openstation status 0042 ready             # backlog → ready
openstation status 42 in-progress         # short ID works
openstation status cli-improvements review
```

---

## `run`

Launch an agent to execute tasks.

### Synopsis

```
openstation run AGENT [flags]             # by-agent mode
openstation run --task TASK [flags]       # by-task mode
```

A positional argument starting with a digit is treated as a task ID (equivalent to `--task`).

### Modes

**Detached (default):** The agent runs autonomously via `-p` (non-interactive) with stream-json capture. Supports budget, turns, and log capture.

**Attached (`--attached`):** Launches an interactive Claude session with task context pre-loaded. Uses `os.execvp` to replace the process. No log capture — Claude's built-in session persistence (`--resume`) provides replay.

**By-agent:** Launches the named agent with the prompt "Execute your ready tasks." Uses `text` output format in detached mode.

**By-task:** Resolves the task, finds ready subtasks (if any), and executes them sequentially with `stream-json` output. If no subtasks exist, executes the task directly. The agent is read from the task's `assignee` field.

### Flags

| Flag                | Default | Description |
|---------------------|---------|-------------|
| `--task TASK`       | —       | Task ID or slug (explicit by-task mode) |
| `-a`, `--attached`  | —       | Interactive mode (replace process, no log capture) |
| `--budget USD`      | `5`     | Max USD per invocation (detached only) |
| `--turns N`         | `50`    | Max turns per invocation (detached only) |
| `--max-tasks N`     | `1`     | Max subtasks to execute (detached only) |
| `--force`           | —       | Skip task status checks (allow non-ready tasks) |
| `--dry-run`         | —       | Print the command without executing |
| `-q`, `--quiet`     | —       | Suppress progress output (detached only) |
| `-j`, `--json`      | —       | Structured JSON dry-run output (detached only) |

### Incompatibilities

| Combination | Behavior |
|-------------|----------|
| `--attached` + `--json` | Error: "JSON output not supported in attached mode" |
| `--attached` + `--quiet` | Error: "Quiet mode not supported in attached mode" |
| `--attached` + `--budget` | Warning to stderr, flag ignored |
| `--attached` + `--turns` | Warning to stderr, flag ignored |
| `--attached` + `--max-tasks` | Warning to stderr, flag ignored |
| `--attached` + `--dry-run` | Allowed — prints the command that would be `execvp`'d |
| `--attached` + task with subtasks | Error with hint to target a specific subtask |

### Examples

```bash
openstation run researcher --attached       # interactive agent session
openstation run --task 0042 --attached      # interactive task session
openstation run --task 0042                 # autonomous (detached)
openstation run --task 0042 --attached --dry-run  # preview attached command
openstation run researcher --dry-run        # show command without executing
openstation run --task 42 --dry-run --json  # structured JSON dry-run output
```

### Logs

By-task detached execution writes stream-json output to `artifacts/logs/<task-name>.jsonl`. Session IDs are extracted and displayed for resumption via `claude --resume <session-id>`. Attached mode does not capture logs.

---

## `agents`

Manage and inspect agent specs from `artifacts/agents/`.

### Synopsis

```
openstation agents [list] [--json | --quiet]
openstation agents show <name> [--json | --vim]
```

Bare `openstation agents` (no sub-action) defaults to `list`.

### Sub-Actions

#### `agents list` (default)

List all agents with name and description.

| Flag | Short | Description |
|------|-------|-------------|
| `--json` | `-j` | JSON array of agent objects |
| `--quiet` | `-q` | One agent name per line (pipe-friendly) |

`--json` and `--quiet` are mutually exclusive.

#### `agents show <name>`

Display the full agent spec (frontmatter + body).

| Flag | Description |
|------|-------------|
| `--json` | Frontmatter fields + `body` key as JSON object |
| `--vim` | Open spec file in `$EDITOR` (default: vim) |

Exit code 3 if agent not found (hints available agents).

### Examples

```bash
openstation agents                          # list all agents (default)
openstation agents list                     # same as bare 'agents'
openstation agents list --json              # JSON array of agent objects
openstation agents list --quiet             # one name per line
openstation agents show researcher          # print full agent spec
openstation agents show researcher --json   # frontmatter + body as JSON
openstation agents show researcher --vim    # open in editor
```

---

## `init`

Initialize Open Station in the current directory.

### Synopsis

```
openstation init [--agents NAMES | --no-agents] [--dry-run] [--force]
```

### What It Does

1. Creates the `.openstation/` directory structure and `.claude/`
2. Copies commands, skills, and docs from the install cache (`$OPENSTATION_DIR` or `~/.local/share/openstation`)
3. Installs agent templates (adapted for the project name)
4. Creates `.claude/` symlinks → `.openstation/` for agent, command, and skill discovery

### Flags

| Flag              | Description |
|-------------------|-------------|
| `--agents NAMES`  | Comma-separated agent names to install (default: all available templates) |
| `--no-agents`     | Skip installing agent specs |
| `--dry-run`       | Show what would be done without writing |
| `--force`         | Overwrite existing user-owned files |

`--agents` and `--no-agents` are mutually exclusive.

### Default Agents

When no filter is specified: `architect`, `author`, `developer`, `project-manager`, `researcher`.

### Examples

```bash
openstation init                          # full init with all agents
openstation init --agents researcher,author
openstation init --no-agents
openstation init --dry-run                # preview without writing
```

### Guards

- Refuses to run inside the Open Station source repo itself.
- Requires the install cache to exist (prompts to run the installer if missing).

---

## Exit Codes

| Code | Constant              | Meaning |
|------|-----------------------|---------|
| 0    | `EXIT_OK`             | Success |
| 1    | `EXIT_USAGE`          | Invalid arguments or usage error |
| 2    | `EXIT_NO_PROJECT`     | Not in an Open Station project (no `.openstation/` found) |
| 3    | `EXIT_NOT_FOUND`      | Task or agent not found |
| 4    | `EXIT_AMBIGUOUS`      | Ambiguous task query (multiple matches) |
| 5    | `EXIT_TASK_NOT_READY` | Task status is not `ready` (use `--force` to override) |
| 6    | `EXIT_INVALID_TRANSITION` | Invalid lifecycle status transition |
| 7    | `EXIT_NO_CLAUDE`      | `claude` CLI not found on `$PATH` |
| 8    | `EXIT_AGENT_ERROR`    | Agent execution failed (non-zero exit from claude) |
| 9    | `EXIT_SOURCE_GUARD`   | Refused to init inside the source repo |

## Project Discovery

All commands except `init` require an Open Station project root. The CLI walks up from `$CWD` looking for:

1. A directory containing both `agents/` and `install.sh` (source repo — prefix: `""`)
2. A `.openstation/` subdirectory (installed project — prefix: `".openstation"`)

If the walk-up finds nothing and `$CWD` is inside a git worktree, the main worktree root is checked as a fallback.
