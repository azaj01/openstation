---
kind: spec
name: autonomous-pipeline
created: 2026-03-20
status: draft
---

# Autonomous Pipeline

Enable fully autonomous task lifecycle — execute, verify,
complete, and create follow-up tasks — using composable
lifecycle hooks as the orchestration layer.

## Problem

Today, running a task through its full lifecycle requires
multiple manual invocations:

```bash
openstation run --task 42              # execute (ready → review)
openstation run --task 42 --verify     # verify  (review → verified)
openstation status 42 done             # complete (verified → done)
```

Each step is a separate human action. We need a way for the
lifecycle to drive itself: when an agent finishes work and
sets `review`, verification should start automatically; when
verification passes, the task should complete automatically.

## Design Principle

**Hooks are the orchestration layer.** Instead of a monolithic
pipeline command that hardcodes "execute → verify → done" in
Python, the lifecycle emerges from composable hook scripts
wired up in `settings.json`. Each hook handles one transition;
chaining them creates the full pipeline.

This means:
- Users choose which steps to automate (wire up the hooks
  they want)
- Each step is independently testable and replaceable
- The existing `openstation run` is the only entry point
- No new orchestration code — hooks are the orchestration

---

## Architecture

### Hook-Driven Lifecycle

```
openstation run --task X
│
│  Agent executes task, then calls:
│  openstation status X review
│
├─ status written: review ──────────────────────────┐
│                                                    │
│  post-hook fires: auto-verify                      │
│  (backgrounds itself, exits 0 immediately)         │
│                                                    │
│  ┌─────────────────────────────────────────────┐   │
│  │  Background: openstation run --task X        │   │
│  │              --verify                        │   │
│  │                                              │   │
│  │  Verifier checks work, then calls:           │   │
│  │  openstation status X verified               │   │
│  │                                              │   │
│  │  ├─ status written: verified ────────────┐   │   │
│  │  │                                       │   │   │
│  │  │  post-hook: auto-done                 │   │   │
│  │  │  openstation status X done            │   │   │
│  │  │                                       │   │   │
│  │  │  ├─ status written: done ─────────┐   │   │   │
│  │  │  │                                │   │   │   │
│  │  │  │  post-hook: auto-commit        │   │   │   │
│  │  │  │  post-hook: create-downstream  │   │   │   │
│  │  │  └────────────────────────────────┘   │   │   │
│  │  └───────────────────────────────────────┘   │   │
│  └──────────────────────────────────────────────┘   │
│                                                     │
└─ Agent session ends (not blocked by hooks)          │
                                                      │
```

### Key Insight: Sync vs Background

The **auto-verify** hook must not block the executing agent's
session. Verification is long-running (minutes). If it ran
synchronously inside the `openstation status X review`
post-hook, the executing agent's claude session would be
frozen waiting for verification to finish.

Solution: the auto-verify hook script backgrounds itself and
exits 0 immediately. The executing agent's session ends
normally. Verification runs as an independent process.

All other hooks (auto-done, auto-commit, create-downstream)
are fast and run synchronously. They fire inside the verify
process, which is already a background job.

```
auto-verify:        BACKGROUND  (spawns new process, exits 0)
auto-done:          SYNC        (fast — one status write)
auto-commit:        SYNC        (< 2 min — claude commits)
create-downstream:  SYNC        (fast — file creation)
```

### Layer Diagram

```
┌──────────────────────────────────────────────┐
│  Entry Points                                 │
│                                               │
│  openstation run --task X     (single task)   │
│  openstation batch            (multiple tasks) │
└───────┬──────────────────────────┬────────────┘
        │                          │
        ▼                          ▼
┌──────────────────┐    ┌──────────────────────┐
│  Agent Execution  │    │  Task Discovery Loop  │
│  (claude -p)      │    │  (Python, no AI)      │
│                   │    │  Iterates ready tasks  │
│  Sets → review    │    │  Calls run per task    │
└────────┬─────────┘    └──────────────────────┘
         │
         ▼
┌──────────────────────────────────────────────┐
│  Lifecycle Hooks (settings.json)              │
│                                               │
│  →review:    auto-verify  (background)        │
│  →verified:  auto-done    (sync)              │
│  →done:      auto-commit  (sync)              │
│  →done:      create-downstream (sync)         │
└──────────────────────────────────────────────┘
```

---

## Hook Scripts

### C1: `auto-verify`

**File:** `bin/hooks/auto-verify`

**Trigger:** `*→review`, phase `post`

**Behavior:**
1. Guard: skip if `OS_HOOK_DEPTH` > 0 (prevent cascading
   re-verification)
2. Guard: skip if `claude` not on `$PATH`
3. Resolve verify agent:
   a. Read task's `owner` field from `$OS_TASK_FILE`
   b. If owner is empty or `user`, read `settings.verify.agent`
   c. Fallback: `project-manager`
4. Guard: skip if verify agent == task's `assignee` (self-
   verification ban). Log warning, exit 0.
5. Background: `nohup openstation run --task "$OS_TASK_NAME"
   --verify > "$LOG_DIR/$OS_TASK_NAME.verify.log" 2>&1 &`
6. Write PID to `$LOG_DIR/$OS_TASK_NAME.verify.pid`
7. Exit 0 immediately

**Log location:** `artifacts/logs/<task-name>.verify.log`

**Self-verification ban:** If the assignee and verify agent
are the same, the hook exits without verifying. This enforces
the lifecycle rule "agents must NOT self-verify" at the
automation layer. The task stays in `review` for human
intervention or a different agent.

### C2: `auto-done`

**File:** `bin/hooks/auto-done`

**Trigger:** `*→verified`, phase `post`

**Behavior:**
1. Guard: skip if `OS_HOOK_DEPTH` > max (safety limit)
2. Run: `openstation status "$OS_TASK_NAME" done`
3. Exit with the status command's exit code

This is synchronous because `openstation status` is fast
(frontmatter write + hook dispatch). It runs inside the
verify process (which is already backgrounded), so it
doesn't block anything.

### C3: `auto-commit`

Already designed in `docs/hooks.md`. No changes needed.

**Trigger:** `*→done`, phase `post`, timeout 120

### C4: `create-downstream`

**File:** `bin/hooks/create-downstream`

**Trigger:** `*→done`, phase `post`

**Behavior:**
1. Read `$OS_TASK_FILE`
2. Extract `## Downstream` section (markdown bullets)
3. For each bullet:
   - `openstation create "<bullet text>" --parent "$OS_TASK_NAME"`
4. Exit 0 (failures to create individual tasks are warnings)

**Created tasks start in `backlog`** — they are not promoted
to `ready` automatically. A human or project-manager decides
when to schedule them.

---

## Hook Wiring

Users enable the pipeline by adding hooks to `settings.json`:

### Minimal (execute + verify only)

```json
{
  "hooks": {
    "StatusTransition": [
      {
        "matcher": "*->review",
        "command": "bin/hooks/auto-verify",
        "phase": "post",
        "timeout": 10
      }
    ]
  }
}
```

### Full pipeline

```json
{
  "hooks": {
    "StatusTransition": [
      {
        "matcher": "*->review",
        "command": "bin/hooks/auto-verify",
        "phase": "post",
        "timeout": 10
      },
      {
        "matcher": "*->verified",
        "command": "bin/hooks/auto-done",
        "phase": "post",
        "timeout": 30
      },
      {
        "matcher": "*->done",
        "command": "bin/hooks/auto-commit",
        "phase": "post",
        "timeout": 120
      },
      {
        "matcher": "*->done",
        "command": "bin/hooks/create-downstream",
        "phase": "post",
        "timeout": 30
      }
    ]
  }
}
```

Note: `auto-verify` has a short timeout (10s) because it
backgrounds the actual work and exits immediately. The other
hooks run synchronously within the background verify process.

---

## Batch Command

The hook scripts handle per-task lifecycle. A thin batch
command handles multi-task discovery and iteration.

### CLI

```
openstation batch [OPTIONS]
```

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--assignee` | string | — | Only run tasks assigned to this agent |
| `--parent` | string | — | Run ready subtasks of this parent |
| `--max-tasks` | int | `5` | Max tasks to kick off |
| `--budget` | float | `5` | Passed through to each `run` |
| `--turns` | int | `50` | Passed through to each `run` |
| `--dry-run` | flag | `false` | Show tasks without executing |
| `--json` | flag | `false` | JSON output |
| `--quiet` | flag | `false` | Minimal output |
| `--wait` | flag | `false` | Wait for all verify processes to finish |

### Behavior

```python
def cmd_batch(args, root):
    # 1. Discover ready tasks (filtered by assignee/parent)
    # 2. Limit to --max-tasks
    # 3. For each task:
    #    a. openstation run --task <name>  (detached)
    #    b. Record result (execution only)
    #    c. If hooks are wired, verify/done happen asynchronously
    # 4. Print summary of executions kicked off
    # 5. If --wait: poll for verify PID files to finish
```

The batch command is **thin** — ~100 lines. It reuses
`run_single_task()` from `run.py` for each task. It does
NOT handle verify or done — hooks do that.

### Why batch is separate from hooks

Hooks fire on transitions. "Run all ready tasks" is not a
transition — it's task discovery. That's a different concern
from lifecycle orchestration. The batch command owns discovery;
hooks own lifecycle.

### `--wait` mode

When `--wait` is set, the batch command polls the PID files
written by `auto-verify` and waits for all background verify
processes to finish before printing the final summary. This
gives a synchronous experience when wanted.

```
batch  5 ready tasks (--wait)
──────────────────────────────────

[1/5] 0042-add-login-page
  execute   ✓  (exit 0, 2m 14s)
  verify    ⏳ (background, pid 12345)

[2/5] 0043-fix-header-alignment
  execute   ✓  (exit 0, 1m 02s)
  verify    ⏳ (background, pid 12346)

waiting for verification...

[1/5] 0042-add-login-page      → done     (3m 01s)
[2/5] 0043-fix-header-alignment → failed   (1m 45s)

──────────────────────────────────
summary   1 done, 1 failed, 3 remaining
```

Without `--wait`, the batch command prints execution results
and exits. Verify/done happen in the background.

---

## Re-Entrancy Guard

### Problem

Hook cascading can create loops:
- Hook on →review triggers verify
- If verify fails and retries, it might re-trigger the hook
- Or a buggy hook that calls `openstation status` with the
  same transition

### Solution: `OS_HOOK_DEPTH` Environment Variable

The hook system sets `OS_HOOK_DEPTH` in the environment passed
to hook commands. Each hook script can read it.

**Hook system change** (in `hooks.py`):

```python
def _build_hook_env(root, task_name, old, new, task_file):
    env = os.environ.copy()
    env["OS_TASK_NAME"] = task_name
    env["OS_OLD_STATUS"] = old
    env["OS_NEW_STATUS"] = new
    env["OS_TASK_FILE"] = str(task_file.resolve())
    env["OS_VAULT_ROOT"] = str(root.resolve())
    # Re-entrancy tracking
    current_depth = int(os.environ.get("OS_HOOK_DEPTH", "0"))
    env["OS_HOOK_DEPTH"] = str(current_depth + 1)
    return env
```

**Hook script guard pattern:**

```bash
# Guard: prevent cascading re-entry
depth="${OS_HOOK_DEPTH:-0}"
if [ "$depth" -gt 1 ]; then
    echo "skipping: hook depth $depth > 1" >&2
    exit 0
fi
```

**Max depth:** Hook scripts decide their own depth limit.
`auto-verify` uses depth > 1. `auto-done` uses depth > 3.
This is per-script policy, not system-enforced, keeping the
hook system simple.

---

## Hook System Enhancements

### E1: `OS_HOOK_DEPTH` env var

Add cascade depth tracking to `_build_hook_env()` in
`hooks.py`. See Re-Entrancy Guard section above.

One-line change. No new configuration, no API change.

### E2: Task frontmatter in hook env (optional, recommended)

Add `OS_TASK_ASSIGNEE` and `OS_TASK_OWNER` to the hook
environment. The auto-verify script needs these to resolve
the verify agent and enforce the self-verification ban.

Without this, auto-verify must parse the task file itself
(doable but redundant — the hook system already reads
frontmatter context).

```python
# In _build_hook_env, after existing vars:
env["OS_TASK_ASSIGNEE"] = fm.get("assignee", "")
env["OS_TASK_OWNER"] = fm.get("owner", "")
```

**Change scope:** `_build_hook_env` gains two optional
parameters. `run_matched` reads frontmatter when building
env (it already has `task_file`). Backward compatible — the
vars are additive.

### E3: No other hook system changes needed

The existing hook infrastructure handles everything else:
- Per-hook timeouts ✓ (already supported)
- Post-hook failure as warning ✓ (already supported)
- Shell command execution ✓ (already supported)
- Declaration-order firing ✓ (already supported)

---

## Safety

### Budget Caps

`--budget` and `--turns` are per-claude-invocation. Passed
through from batch → run → claude. A task going through
execute + verify costs at most 2x budget.

### Task Count Limit

`--max-tasks` on the batch command caps how many tasks are
kicked off. Default 5.

### No Recursive Execution

`create-downstream` creates tasks in `backlog`, not `ready`.
The batch command only picks up `ready` tasks. No loop.

### Self-Verification Ban

`auto-verify` checks assignee != verify agent before spawning.
If they match, the task stays in `review` for human/different
agent intervention.

### Re-Entrancy Guard

`OS_HOOK_DEPTH` prevents hooks from cascading infinitely.
Each hook script sets its own depth threshold.

### Existing Safety Layers (unchanged)

- Allowed-tools per agent (frontmatter)
- Write-path validation hook
- Destructive-git blocking hook
- Lifecycle transition validation

---

## Settings Extension

Add `pipeline` key to `settings.json` for defaults:

```json
{
  "pipeline": {
    "verify_agent": "project-manager",
    "auto_verify": true,
    "auto_done": true,
    "auto_commit": true,
    "create_downstream": false
  }
}
```

This is **documentation-only** — the actual wiring is in the
`hooks.StatusTransition` array. The `pipeline` key serves as
a reference for what automation is enabled. Hook scripts can
read it for configuration (e.g., auto-verify reads
`pipeline.verify_agent`).

Alternatively, `openstation init` could auto-generate the hook
entries based on `pipeline` settings. **Decision: deferred** —
start with manual hook wiring, add init-time generation if
users find the manual config tedious.

---

## Components

| # | Component | Location | Purpose |
|---|-----------|----------|---------|
| C1 | auto-verify hook | `bin/hooks/auto-verify` | Background verify on →review |
| C2 | auto-done hook | `bin/hooks/auto-done` | Complete on →verified |
| C3 | create-downstream hook | `bin/hooks/create-downstream` | Create follow-up tasks on →done |
| C4 | batch command | `src/openstation/pipeline.py` | Task discovery loop |
| C5 | hook depth tracking | `src/openstation/hooks.py` | `OS_HOOK_DEPTH` env var |
| C6 | hook env extension | `src/openstation/hooks.py` | `OS_TASK_ASSIGNEE`, `OS_TASK_OWNER` |
| C7 | CLI registration | `src/openstation/cli.py` | Register `batch` subcommand |

### Existing (no changes)

| Component | Location | Role |
|-----------|----------|------|
| auto-commit hook | `bin/hooks/auto-commit` | Already designed in hooks.md |
| `run_single_task()` | `src/openstation/run.py` | Execute step |
| `cmd_run --verify` | `src/openstation/run.py` | Verify step |
| `cmd_status` | `src/openstation/tasks.py` | Status transitions + hooks |
| Hook system | `src/openstation/hooks.py` | Load, match, execute hooks |

---

## Build Sequence

```
C5, C6 (hook enhancements) ← foundation, do first
  │
  ├─► C1 (auto-verify)     ← depends on OS_HOOK_DEPTH
  │
  ├─► C2 (auto-done)       ← depends on OS_HOOK_DEPTH
  │
  ├─► C3 (create-downstream)
  │
  └─► C4, C7 (batch command + CLI)
```

C1-C3 are independent shell scripts, can be parallel.
C4 depends on C1 working (for --wait mode PID tracking).

---

## Verification

| Criterion | How to verify |
|-----------|---------------|
| auto-verify backgrounds itself | Hook exits in < 1s; verify PID file written |
| auto-verify enforces self-verify ban | assignee == owner → hook exits, task stays in review |
| auto-verify reads verify agent | settings.verify.agent used when owner is `user` |
| auto-done transitions correctly | Task in `verified` → `done` after hook fires |
| create-downstream parses bullets | `## Downstream` with 3 bullets → 3 backlog tasks created |
| create-downstream sets parent | Created tasks have `parent: "[[original]]"` |
| OS_HOOK_DEPTH increments | Depth 0 in first hook, 1 in cascaded hook |
| Re-entrancy guard works | auto-verify at depth > 1 → exits without spawning |
| batch discovers ready tasks | `--assignee dev` returns only dev's ready tasks |
| batch respects --max-tasks | 10 ready tasks + --max-tasks 3 → 3 executed |
| batch --wait polls PIDs | Waits for all verify processes, prints final statuses |
| batch --dry-run shows plan | Lists tasks + commands without executing |
| Hooks composable | User wires only auto-verify → tasks reach review, get verified, stay verified (no auto-done) |
| Full chain works end-to-end | ready → review → verified → done → commit, all via hooks |

---

## Design Decisions

### DD-1: Hooks as orchestration, not a pipeline command

The lifecycle chain (verify → done → commit) is expressed as
hook configuration, not as Python control flow in a pipeline
module.

**Trade-off:** Users must configure hooks in `settings.json`
(more setup) but get full composability (pick which steps to
automate). A monolithic pipeline command would be easier to
start but harder to customize.

**Why this is better:** Open Station is convention-first. Hooks
are already the convention for lifecycle automation. Building
a parallel orchestration system creates two ways to do the
same thing. Hooks are the one way.

### DD-2: auto-verify backgrounds itself

The hook script forks `openstation run --verify` into the
background and exits 0 immediately. This prevents the
executing agent's session from blocking on verification.

**Trade-off:** Fire-and-forget means the executing session
doesn't know if verification succeeded. Acceptable because:
(a) the batch command's `--wait` mode can track it via PIDs,
(b) `openstation list` always shows current status, and
(c) post-hooks on →done provide notification hooks.

### DD-3: Thin batch command, not smart orchestrator

The `batch` command does only task discovery + iteration. It
calls `openstation run --task X` for each task and moves on.
All lifecycle logic lives in hooks.

**Trade-off:** The batch command can't print a unified
"pipeline complete" summary unless `--wait` is used. This is
the cost of decoupling discovery from lifecycle. The `--wait`
flag bridges the gap when needed.

### DD-4: Re-entrancy via env var, not system-enforced limit

`OS_HOOK_DEPTH` is tracked by the hook system but the depth
limit is per-script policy. The hook system does not enforce
a global max depth.

**Trade-off:** A buggy hook script that ignores the depth var
could loop. Acceptable because: (a) shipped hook scripts all
check it, (b) budget caps on claude limit damage, and (c) a
system-enforced limit would need configuration and edge-case
handling for legitimate deep chains.

### DD-5: auto-done is a separate hook, not part of auto-verify

auto-verify runs verification. auto-done transitions to done.
They could be combined (verify script also sets done) but
separating them means users can enable verification without
auto-completion — useful when a human wants to review verified
tasks before marking done.

### DD-6: create-downstream creates backlog, not ready

Follow-up tasks start in `backlog`. This prevents runaway
execution where agents create tasks that get immediately
executed, which create more tasks. A human or project-manager
promotes to `ready` when appropriate.
