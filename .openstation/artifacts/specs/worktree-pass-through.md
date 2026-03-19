---
kind: spec
name: worktree-pass-through
agent: architect
task: "[[0124-spec-worktree-integration]]"
created: 2026-03-13
---

# Worktree Pass-Through (M1)

Design for running Open Station agents inside git worktrees.
Scoped to Milestone 1 only: vault resolution and `--worktree`
flag pass-through. No branch-scoped task filtering, no custom
worktree lifecycle management, no parallel orchestration.

---

## 1. Vault Resolution from Worktrees (`find_root()`)

### 1.1 Current State — Already Implemented

`core.py` lines 85–132 implement a two-phase vault discovery:

1. **Walk-up phase.** Starting from CWD, walk parent directories
   looking for `.openstation/` (installed project) or source repo
   markers (`agents/` + `install.sh`).

2. **Git fallback phase.** If the walk-up finds nothing, call
   `git rev-parse --git-common-dir` to resolve the main worktree
   root, then check that directory for Open Station markers.

```
CWD: /repo/.claude/worktrees/task-0042/
  ↓ walk-up: no .openstation/ found
  ↓ git rev-parse --git-common-dir → /repo/.git
  ↓ parent of .git → /repo/
  ↓ _check_dir(/repo/) → found .openstation/ → ✓
```

### 1.2 Design Decision: No Changes Needed

**Status: Decided.**

The existing `find_root()` implementation handles worktrees
correctly. An agent launched inside a Claude-managed worktree
(under `.claude/worktrees/<name>/`) or a manually created
worktree (sibling directory) will resolve the vault from the
main worktree root.

**Edge cases already handled:**

| Scenario | Behavior |
|----------|----------|
| CWD is inside `.claude/worktrees/<name>/` | Walk-up fails, git fallback finds main root |
| CWD is a sibling worktree (`../repo-task-42/`) | Walk-up fails, git fallback finds main root |
| Git is unavailable | `_git_main_worktree_root` returns `None`, `find_root()` returns `(None, None)` — clean error |
| Not inside a git repo | Same as above |

**No code changes required for `find_root()`.**

### 1.3 Artifact Path Resolution

When agents produce artifacts, they write to paths relative to
the vault root (e.g., `artifacts/specs/foo.md`). Since
`find_root()` returns the main worktree root, all artifact
paths resolve correctly — artifacts are written to the shared
vault, not the worktree-local directory.

The `tasks_dir_path()` helper already computes paths relative
to the resolved root, so task discovery and artifact routing
work unchanged.

---

## 2. `--worktree` Pass-Through on `openstation run`

### 2.1 Approach: Delegate to Claude CLI

**Status: Decided.**

`openstation run` adds a `--worktree` flag that is forwarded
directly to the `claude` CLI. Open Station does not create,
manage, or clean up worktrees — Claude handles the full
lifecycle.

**Rationale:**
- Zero new dependencies or subprocess management
- Leverages Claude's built-in worktree creation and cleanup
- Minimal code change (flag plumbing only)
- Claude prompts the user about cleanup when changes exist

**Trade-off accepted:** Branch names follow Claude's convention
(`worktree-<name>`) rather than a task-aligned scheme like
`task/0042-slug`. This is acceptable for M1; custom branch
naming is deferred to M2+ if needed.

### 2.2 CLI Interface

```
openstation run --task <id> --worktree [<name>] [--attached]
openstation run <agent> --worktree [<name>] [--attached]
```

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--worktree` | optional string | (auto) | Worktree name passed to `claude --worktree <name>` |

**Worktree name derivation** (when `--worktree` is given
without a name):

| Mode | Derived Name |
|------|-------------|
| By-task | Task name: `0042-add-auth` |
| By-agent | Agent name: `researcher` |

Examples:

```bash
# Explicit name
openstation run --task 0042 --worktree my-feature --attached

# Auto-derived name (uses task name "0042-add-auth")
openstation run --task 0042 --worktree --attached

# Agent mode with auto name
openstation run researcher --worktree --attached
```

### 2.3 Implementation: `build_command()` Changes

Add a `worktree` parameter to `build_command()`:

```python
def build_command(agent_name, budget, turns, prompt, tools,
                  output_format="json", attached=False,
                  dangerously_skip_permissions=False,
                  worktree=None):
```

Insert `--worktree <name>` into the command before other flags:

```python
if worktree:
    cmd.extend(["--worktree", worktree])
```

**Placement in argv** (both attached and detached):

```
claude --worktree <name> --agent <agent> [other flags...]
```

The `--worktree` flag goes immediately after `claude`, before
`--agent`, so Claude creates the worktree before loading the
agent spec.

### 2.4 Implementation: `cmd_run()` Changes

Add worktree argument parsing and plumb through to execution:

```python
# In cmd_run():
worktree = getattr(args, "worktree", None)

# Derive name when --worktree is given without a value
if worktree is True:  # argparse: nargs="?" with const=True
    if task_ref:
        worktree = task_name  # resolved task name
    elif agent_name:
        worktree = agent_name
```

Pass `worktree` to `build_command()`, `_exec_or_run()`, and
`run_single_task()`.

### 2.5 Implementation: `cli.py` Changes

Add the `--worktree` argument to the `run` subparser:

```python
run_p.add_argument(
    "-w", "--worktree",
    nargs="?",
    const=True,
    default=None,
    metavar="NAME",
    help="Run in a Claude worktree (optional name, default: auto-derived)",
)
```

Using `nargs="?"` with `const=True`:
- `--worktree` alone → `args.worktree = True` (auto-derive)
- `--worktree my-name` → `args.worktree = "my-name"`
- (omitted) → `args.worktree = None` (no worktree)

### 2.6 Compatibility Matrix

| Mode | `--worktree` | Behavior |
|------|-------------|----------|
| Attached, by-task | ✅ | `os.execvp(claude --worktree <name> --agent ...)` |
| Attached, by-agent | ✅ | Same |
| Detached, by-task | ✅ | `subprocess.Popen(claude --worktree <name> -p ...)`, log capture works unchanged |
| Detached, by-agent | ✅ | Same |
| Dry-run | ✅ | Printed command includes `--worktree` |
| Subtask dispatch | ✅ | Each subtask gets the same worktree name (sequential execution, one at a time) |

### 2.7 Detached Mode Consideration

In detached mode, `_stream_and_capture` launches Claude as a
subprocess and reads stdout. When `--worktree` is added, Claude
creates the worktree before starting the session. The stdout
stream-json protocol is unchanged — `session_id` and `result`
messages flow the same way.

Claude handles worktree cleanup after the session ends (removes
if no changes, prompts/keeps if changes exist). No cleanup
code needed in Open Station.

---

## 3. Agent Vault Discovery in Worktrees

### 3.1 How It Works

When `openstation run --task 0042 --worktree` launches Claude:

1. Claude creates worktree at `.claude/worktrees/<name>/`
2. Claude starts a session with CWD inside the worktree
3. The agent's skill (`openstation-execute`) calls
   `openstation list` or reads `artifacts/tasks/`
4. The `openstation` CLI calls `find_root()`, which:
   - Walks up from worktree CWD — no `.openstation/` found
   - Falls back to `git rev-parse --git-common-dir`
   - Resolves main worktree root → finds `.openstation/`
5. All task discovery, artifact reads, and artifact writes
   resolve against the shared vault in the main worktree

### 3.2 File Reads via Agent Tools

Agents use `Read`, `Glob`, and `Grep` tools to access files.
These tools operate on absolute or relative paths. Since the
vault is in the main worktree (not the linked worktree), agents
must reference vault files by absolute path or by paths
relative to the main worktree root.

**How this works in practice:**
- `openstation list` and `openstation show` output paths
  relative to the vault root — agents use these as-is
- The prompt says `artifacts/tasks/0042-slug.md` — this path
  resolves from the main worktree root, not the linked worktree
- Claude Code's file tools resolve relative paths from the
  project root, which for a worktree is the worktree directory

**Potential issue:** If Claude resolves relative paths from the
worktree CWD, `artifacts/tasks/0042.md` won't exist there.

**Mitigation:** The `openstation` CLI always resolves paths via
`find_root()`, so CLI-based operations work. For direct file
reads in agent prompts, the path in the prompt
(`artifacts/tasks/0042-slug.md`) may need to be absolute.

**Status: Needs validation.** Test whether Claude's `Read` tool
resolves paths from the worktree root or the main repo root
when running in a worktree. If worktree-relative, the prompt
template in `run.py` should emit absolute paths. This is a
low-risk change:

```python
# Current
prompt = f"Execute task {task_name}. Read its spec at "
         f"artifacts/tasks/{task_name}.md ..."

# If absolute paths needed
prompt = f"Execute task {task_name}. Read its spec at "
         f"{tasks_dir / task_name}.md ..."
```

---

## 4. Milestone Boundaries — What Ships in M1

### 4.1 In Scope

| Item | Component | Status |
|------|-----------|--------|
| `find_root()` worktree fallback | `core.py` | Done — no changes |
| `--worktree` / `-w` flag on `openstation run` | `cli.py` | New |
| `--worktree` pass-through to `build_command()` | `run.py` | New |
| Worktree name auto-derivation | `run.py` | New |
| Dry-run output includes `--worktree` | `run.py` | New |
| Validate agent file access from worktree | Manual test | New |

### 4.2 Out of Scope (Deferred)

| Item | Milestone | Reason |
|------|-----------|--------|
| `branch` frontmatter field | M2 | Requires schema change, filtering logic |
| `--branch auto` task filtering | M2 | Depends on `branch` field |
| Custom branch naming (`task/0042-slug`) | M2+ | Requires Option B (pre-create worktrees) |
| Worktree creation by `openstation run` | M2+ | Requires subprocess lifecycle management |
| Worktree cleanup by `openstation run` | M2+ | Tied to custom creation |
| `--tmux` pass-through | Future | Separate concern, needs investigation |
| Parallel subtask execution (`--parallel`) | M3+ | Process pool, log mux, failure handling |
| Agent skills documenting worktree workflows | M3 | Depends on M1 usability feedback |
| worktrunk/workmux integration | Never | Document coexistence, not dependency |

### 4.3 Acceptance Criteria

1. `openstation run --task 0042 --worktree --attached` launches
   Claude in a worktree and the agent can find and read the
   task spec from the shared vault
2. `openstation run --task 0042 --worktree` (detached) produces
   a log file in the vault's `artifacts/logs/`
3. `openstation run researcher --worktree --attached` works in
   by-agent mode
4. `openstation run --task 0042 --worktree --dry-run` prints
   the command with `--worktree <name>` included
5. `openstation run --task 0042 --worktree my-branch --attached`
   passes `my-branch` as the worktree name

---

## 5. Schema and Documentation Changes

### 5.1 Files to Modify

| File | Change |
|------|--------|
| `src/openstation/cli.py` | Add `--worktree` / `-w` argument to `run` subparser |
| `src/openstation/run.py` | Add `worktree` param to `build_command()`, `_exec_or_run()`, `run_single_task()`, `cmd_run()` |
| `CLAUDE.md` | Add `--worktree` to the CLI reference in the managed section |
| `docs/task.spec.md` | No changes (no new frontmatter fields in M1) |
| `docs/lifecycle.md` | No changes |
| `docs/storage-query-layer.md` | No changes |

### 5.2 CLAUDE.md Updates

Add worktree examples to the CLI reference:

```markdown
## Running an Agent

```bash
openstation run researcher --attached      # interactive session
openstation run --task 0042 --attached     # interactive task session
openstation run --task 0042                # autonomous (detached)
openstation run --task 0042 --worktree --attached  # in a worktree
```
```

### 5.3 No New Frontmatter Fields

M1 introduces no schema changes. The `branch` frontmatter field
is M2 scope. The `--worktree` flag is a CLI-only concern that
maps to Claude CLI behavior, not to task metadata.

---

## 6. Open Items for Post-M1 Review

After M1 ships and is usability-tested, revisit:

1. **Path resolution in worktrees** — confirm whether agent
   `Read` tool resolves `artifacts/tasks/...` correctly from
   a worktree CWD. If not, switch prompt to absolute paths.

2. **Subtask dispatch with worktrees** — in detached mode with
   subtasks, should each subtask get its own worktree name
   (e.g., `0043-subtask-a`, `0044-subtask-b`) or share one?
   M1 uses the parent task name for all; revisit if isolation
   is needed.

3. **Branch naming conventions** — if `worktree-<task-name>` is
   awkward, consider M2 Option B (pre-create with custom branch
   names like `task/0042-slug`).

4. **`--tmux` flag** — investigate whether `--tmux` combined
   with `--worktree` works for fully detached parallel sessions.

5. **Agent teams** — Claude's agent teams feature may overlap
   with Open Station's multi-agent model. Monitor for public
   docs.
