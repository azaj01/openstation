---
kind: spec
name: hook-based-autonomous-chaining
agent: architect
task: "[[0208-spec-hook-based-autonomous-chaining]]"
created: 2026-03-22
---

# Hook-Based Autonomous Chaining

Design spec for automatic task lifecycle chaining via
post-transition hooks. The only human touchpoint is promoting a
task to `ready` — everything after that is autonomous.

```
MANUAL              AUTO            AUTO           AUTO
backlog → ready → in-progress → review → verified → done
            ↑         ↑              ↑         ↑
          human    hook:start     hook:verify hook:accept
```

---

## 1. Tmux Dispatch Helper

A shared bash script that spawns a command in a named tmux
window with `CLAUDECODE` cleared. Reusable by both this feature
and 0199 (tmux for detached runs).

### 1.1 Location

```
bin/os-dispatch
```

Executable, on `$PATH` when running from the source repo. For
installed projects, symlinked to `.openstation/bin/os-dispatch`.

### 1.2 Interface

```bash
os-dispatch <window-name> <command...>
```

- **`window-name`** — tmux window name (must be unique within
  the session).
- **`command...`** — the command and arguments to run inside the
  new tmux window.

Exit codes:

| Code | Meaning |
|------|---------|
| 0 | Command dispatched (tmux or nohup fallback) |
| 1 | Missing arguments |

### 1.3 Session/Window Naming Convention

- **Window name**: Caller provides it. Hook scripts use the
  pattern `os-<task-name>` (e.g., `os-0042-cli-improvements`).
- **Session**: Uses the *current* tmux session (the one the hook
  is running inside). `os-dispatch` does not create sessions — it
  creates windows within the existing session.

Rationale: agents already run in tmux sessions. Creating windows
in the same session keeps all agent work visible in one place.

### 1.4 Tmux Availability Detection

```bash
if tmux info >/dev/null 2>&1; then
  # tmux is available — use new-window
else
  # fallback to nohup
fi
```

`tmux info` succeeds only when a tmux server is running *and*
the current shell is inside a tmux session (has `$TMUX` set) or
can reach the server. This is the correct check because
`new-window` requires an active session context.

### 1.5 Duplicate Window Names

Tmux allows duplicate window names, so `new-window -n "os-X"`
will succeed even if a window named `os-X` already exists. This
is acceptable because:

- Two tasks with the same name cannot exist (IDs are unique)
- The `*→ready` hook fires once per promotion
- If a stale window exists from a crashed prior run, the new
  window coexists harmlessly

No deduplication logic needed.

### 1.6 nohup Fallback

When tmux is unavailable:

```bash
LOG_DIR="${OS_VAULT_ROOT:-.}/.openstation/logs"
mkdir -p "$LOG_DIR"
(env -u CLAUDECODE nohup "$@" \
  > "$LOG_DIR/dispatch-${window_name}.log" 2>&1 &)
```

Logs go to `.openstation/logs/dispatch-<name>.log`. The subshell
+ `&` pattern detaches the process. `env -u CLAUDECODE` strips
the guard variable.

### 1.7 Full Script

```bash
#!/usr/bin/env bash
# os-dispatch — spawn a command in a named tmux window or nohup fallback.
# Usage: os-dispatch <window-name> <command...>
set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "usage: os-dispatch <window-name> <command...>" >&2
  exit 1
fi

WINDOW_NAME="$1"; shift

if tmux info >/dev/null 2>&1; then
  tmux new-window -n "$WINDOW_NAME" \
    -e "CLAUDECODE=" \
    -e "OS_HOOK_DEPTH=${OS_HOOK_DEPTH:-0}" \
    "$@"
else
  LOG_DIR="${OS_VAULT_ROOT:-.}/.openstation/logs"
  mkdir -p "$LOG_DIR"
  (env -u CLAUDECODE nohup "$@" \
    > "$LOG_DIR/dispatch-${WINDOW_NAME}.log" 2>&1 &)
  echo "os-dispatch: tmux unavailable, launched via nohup (log: $LOG_DIR/dispatch-${WINDOW_NAME}.log)"
fi
```

### 1.8 Error Handling

| Scenario | Behavior |
|----------|----------|
| tmux server not running | Falls through to nohup |
| `$TMUX` not set (not in tmux) | `tmux info` may still work if server is running; if not, nohup |
| `new-window` fails | Non-zero exit propagates to caller (hook reports warning) |
| nohup command not found | Unlikely (`nohup` is POSIX); script exits non-zero |
| Log directory not writable | `mkdir -p` fails, script exits non-zero |

---

## 2. Hook Scripts

Three hook scripts in `bin/hooks/`, following the pattern of
existing scripts (`auto-commit`, `suspend`).

### 2.1 Auto-Start: `bin/hooks/auto-start`

**Trigger**: `*→ready` (post-hook)

**Action**: Dispatch `openstation run --task $OS_TASK_NAME --attached`
in a new tmux window.

```bash
#!/usr/bin/env bash
# Auto-start — dispatch agent execution when a task reaches ready.
set -euo pipefail

# ── Guards ──────────────────────────────────────────────────
for var in OS_TASK_NAME OS_TASK_FILE OS_VAULT_ROOT; do
  if [[ -z "${!var:-}" ]]; then
    echo "auto-start: missing required env var $var" >&2
    exit 1
  fi
done

# ── Opt-in check ────────────────────────────────────────────
# Only fire if autonomous chaining is enabled in settings
ENABLED=$(python3 -c "
import json, sys
try:
    data = json.load(open('${OS_VAULT_ROOT}/.openstation/settings.json'))
except Exception: data = {}
print(data.get('autonomous', {}).get('enabled', False))
" 2>/dev/null || echo "False")

if [[ "$ENABLED" != "True" ]]; then
  exit 0
fi

# ── Depth guard ─────────────────────────────────────────────
DEPTH="${OS_HOOK_DEPTH:-0}"
MAX_DEPTH="${OS_MAX_HOOK_DEPTH:-5}"
if (( DEPTH >= MAX_DEPTH )); then
  echo "auto-start: hook depth $DEPTH >= max $MAX_DEPTH, stopping" >&2
  exit 0
fi
export OS_HOOK_DEPTH=$((DEPTH + 1))

# ── Assignee guard ──────────────────────────────────────────
# Skip if no assignee is set (nothing to run)
ASSIGNEE=$(python3 -c "
import yaml, sys
with open('${OS_TASK_FILE}') as f:
    content = f.read()
fm = content.split('---')[1] if '---' in content else ''
data = yaml.safe_load(fm) or {}
print(data.get('assignee') or '')
" 2>/dev/null || echo "")

if [[ -z "$ASSIGNEE" ]]; then
  echo "auto-start: task $OS_TASK_NAME has no assignee, skipping" >&2
  exit 0
fi

# ── Dispatch ────────────────────────────────────────────────
os-dispatch "os-${OS_TASK_NAME}" \
  openstation run --task "$OS_TASK_NAME" --attached
```

**Why post-hook**: The task must already be in `ready` status
when the agent picks it up. A pre-hook would fire before the
status is written.

**Why `--attached`**: Attached mode keeps the agent session
visible and interactive in the tmux window for observability.

### 2.2 Auto-Verify: `bin/hooks/auto-verify`

**Trigger**: `*→review` (post-hook)

**Action**: Dispatch `openstation run --task $OS_TASK_NAME --verify --attached`
in a new tmux window.

```bash
#!/usr/bin/env bash
# Auto-verify — dispatch verification when a task enters review.
set -euo pipefail

# ── Guards ──────────────────────────────────────────────────
for var in OS_TASK_NAME OS_TASK_FILE OS_VAULT_ROOT; do
  if [[ -z "${!var:-}" ]]; then
    echo "auto-verify: missing required env var $var" >&2
    exit 1
  fi
done

# ── Opt-in check ────────────────────────────────────────────
ENABLED=$(python3 -c "
import json, sys
try:
    data = json.load(open('${OS_VAULT_ROOT}/.openstation/settings.json'))
except Exception: data = {}
print(data.get('autonomous', {}).get('enabled', False))
" 2>/dev/null || echo "False")

if [[ "$ENABLED" != "True" ]]; then
  exit 0
fi

# ── Depth guard ─────────────────────────────────────────────
DEPTH="${OS_HOOK_DEPTH:-0}"
MAX_DEPTH="${OS_MAX_HOOK_DEPTH:-5}"
if (( DEPTH >= MAX_DEPTH )); then
  echo "auto-verify: hook depth $DEPTH >= max $MAX_DEPTH, stopping" >&2
  exit 0
fi
export OS_HOOK_DEPTH=$((DEPTH + 1))

# ── Dispatch ────────────────────────────────────────────────
os-dispatch "os-verify-${OS_TASK_NAME}" \
  openstation run --task "$OS_TASK_NAME" --verify --attached
```

### 2.3 Auto-Accept: `bin/hooks/auto-accept`

**Trigger**: `*→verified` (post-hook)

**Action**: Run `openstation status $OS_TASK_NAME done` directly
(no Claude needed — pure CLI call).

```bash
#!/usr/bin/env bash
# Auto-accept — transition verified tasks to done.
set -euo pipefail

# ── Guards ──────────────────────────────────────────────────
for var in OS_TASK_NAME OS_VAULT_ROOT; do
  if [[ -z "${!var:-}" ]]; then
    echo "auto-accept: missing required env var $var" >&2
    exit 1
  fi
done

# ── Opt-in check ────────────────────────────────────────────
ENABLED=$(python3 -c "
import json, sys
try:
    data = json.load(open('${OS_VAULT_ROOT}/.openstation/settings.json'))
except Exception: data = {}
print(data.get('autonomous', {}).get('enabled', False))
" 2>/dev/null || echo "False")

if [[ "$ENABLED" != "True" ]]; then
  exit 0
fi

# ── Depth guard ─────────────────────────────────────────────
DEPTH="${OS_HOOK_DEPTH:-0}"
MAX_DEPTH="${OS_MAX_HOOK_DEPTH:-5}"
if (( DEPTH >= MAX_DEPTH )); then
  echo "auto-accept: hook depth $DEPTH >= max $MAX_DEPTH, stopping" >&2
  exit 0
fi
export OS_HOOK_DEPTH=$((DEPTH + 1))

# ── Direct CLI call (no Claude needed) ──────────────────────
openstation status "$OS_TASK_NAME" done
```

**Key difference**: This hook runs synchronously inline — no
tmux dispatch needed. `openstation status X done` is a fast CLI
call that doesn't spawn Claude.

---

## 3. Chain-Next Hook (Future — Design Only)

**Trigger**: `*→done` (post-hook)

**Action**: Find the parent task, check for the next ready
subtask, dispatch it.

### 3.1 Algorithm

```
1. Read $OS_TASK_FILE frontmatter → extract parent field
2. If no parent → exit 0 (standalone task, nothing to chain)
3. Resolve parent task file
4. Read parent subtasks list
5. For each subtask in order:
   a. Read subtask file → check status
   b. If status == "ready" → dispatch auto-start and exit
6. If no ready subtasks remain:
   a. Check if ALL subtasks are done
   b. If yes → openstation status <parent> review
   c. If no → exit 0 (some subtasks still in-progress/backlog)
```

### 3.2 Naming

`bin/hooks/chain-next`

### 3.3 Design Constraints

- Must parse YAML frontmatter (reuse the Python one-liner
  pattern from other hooks, or call `openstation show --json`)
- Subtask ordering follows the `subtasks` list in the parent
  frontmatter (declaration order = priority order)
- Only dispatches ONE subtask per invocation (serial execution
  by default)

### 3.4 Why Deferred

The chain-next hook requires reading and interpreting multiple
task files, making subtask ordering decisions, and handling the
parent completion logic. This is meaningfully more complex than
the three implemented hooks. Users will promote subtasks to
`ready` manually for now.

---

## 4. Loop Prevention

### 4.1 Mechanism: `OS_HOOK_DEPTH` Environment Variable

Each hook script checks and increments `OS_HOOK_DEPTH` before
dispatching. The dispatch helper (`os-dispatch`) passes the
current depth into the spawned tmux window via `-e`.

```
Hook fires (depth=0)
  → os-dispatch sets OS_HOOK_DEPTH=1 in new window
    → Agent runs, completes, transitions to review
      → Review hook fires (depth=1)
        → os-dispatch sets OS_HOOK_DEPTH=2
          → Verify agent runs, transitions to verified
            → Accept hook fires (depth=2), runs inline
              → done hook fires (depth=3)
                → auto-commit runs (not a dispatch, runs inline)
```

### 4.2 Default Max Depth

**`OS_MAX_HOOK_DEPTH=5`** (configurable via environment).

A normal chain is: ready(0) → run(1) → review(1) → verify(2)
→ verified(2) → done(3). Max observed depth is 3 for a single
task. Setting the limit to 5 provides headroom for the future
chain-next hook (which would add 1-2 more levels per subtask
generation).

### 4.3 Behavior at Max Depth

The hook **exits 0** (success, no-op) — it does not fail. This
prevents the hook from blocking the transition while still
stopping the chain. A log message is printed for observability.

### 4.4 Why Not Clean-Env Isolation?

Alternative considered: spawned sessions run in a completely
clean environment so hooks don't see `OS_HOOK_DEPTH` and
effectively start fresh. **Rejected** because:

- It defeats the purpose — the spawned agent *should* trigger
  hooks (that's the whole chain)
- Clean env would lose all `OS_` context variables
- Depth tracking is explicit and debuggable

### 4.5 Where Depth Propagates

| Mechanism | How depth propagates |
|-----------|---------------------|
| `os-dispatch` (tmux) | `-e "OS_HOOK_DEPTH=N"` on `new-window` |
| `os-dispatch` (nohup) | Inherited from `export OS_HOOK_DEPTH=N` in the hook script |
| Inline CLI calls | Inherited from the current process env |

---

## 5. `_build_hook_env()` Recommendation

### 5.1 Decision: Do NOT Strip `CLAUDECODE`

**Recommendation**: Leave `_build_hook_env()` unchanged. Do not
strip `CLAUDECODE` from the env dict.

### 5.2 Trade-Off Analysis

| Option | Pros | Cons |
|--------|------|------|
| **Strip in `_build_hook_env()`** | Hook scripts don't need to handle it; simpler scripts | Hooks lose the ability to detect they're in a Claude session; breaks hooks that legitimately need this info (e.g., conditional behavior); invisible side effect in a generic function |
| **Strip in `os-dispatch` only** | Targeted — only affects dispatched processes that need it; hooks retain full env context; explicit and visible | Hook scripts that spawn Claude directly (without `os-dispatch`) must handle it themselves |

**Chosen: Strip in `os-dispatch` only.** The dispatch helper is
the right abstraction boundary — it exists specifically to spawn
processes outside the Claude guard. `_build_hook_env()` is a
generic env builder and should not encode dispatch-specific
concerns.

### 5.3 What Changes

- `_build_hook_env()`: No changes.
- `os-dispatch`: Uses `tmux new-window -e "CLAUDECODE="` (tmux
  path) or `env -u CLAUDECODE` (nohup path) to clear the guard.
- Hook scripts: Do not need to touch `CLAUDECODE` — they call
  `os-dispatch` which handles it.

---

## 6. Updated `settings.json`

Full configuration with all three autonomous hooks plus existing
hooks:

```json
{
  "hooks": {
    "StatusTransition": [
      {
        "matcher": "*→ready",
        "command": "bin/hooks/auto-start",
        "phase": "post",
        "timeout": 10
      },
      {
        "matcher": "*→review",
        "command": "bin/hooks/auto-verify",
        "phase": "post",
        "timeout": 10
      },
      {
        "matcher": "*→verified",
        "command": "bin/hooks/auto-accept",
        "phase": "post",
        "timeout": 30
      },
      {
        "matcher": "*→done",
        "command": "bin/hooks/auto-commit",
        "phase": "post",
        "timeout": 120
      },
      {
        "matcher": "in-progress→ready",
        "command": "bin/hooks/suspend",
        "phase": "post",
        "timeout": 120
      },
      {
        "matcher": "in-progress→backlog",
        "command": "bin/hooks/suspend",
        "phase": "post",
        "timeout": 120
      }
    ]
  },
  "autonomous": {
    "enabled": false
  },
  "defaults": {
    "show": { "editor": true }
  }
}
```

### 6.1 Hook Details

| Hook | Matcher | Phase | Timeout | Rationale |
|------|---------|-------|---------|-----------|
| auto-start | `*→ready` | post | 10s | Dispatch is fire-and-forget; should complete in <1s |
| auto-verify | `*→review` | post | 10s | Same — dispatch is instant |
| auto-accept | `*→verified` | post | 30s | Inline CLI call; may trigger its own hooks (auto-commit) |
| auto-commit | `*→done` | post | 120s | Claude agent needs time to review diffs and commit |
| suspend (×2) | `in-progress→ready/backlog` | post | 120s | Existing — may invoke Claude for commit |

### 6.2 Ordering

Autonomous hooks are listed first. The `*→done` auto-commit
hook fires after auto-accept because auto-accept transitions
`verified→done`, which triggers the `*→done` matcher.

### 6.3 Hook Interaction Chain

```
*→ready (auto-start)
  ↓ dispatches agent
  Agent works...
  Agent calls: openstation status X review
    ↓
    *→review (auto-verify)
      ↓ dispatches verify agent
      Verify agent calls: openstation status X verified
        ↓
        *→verified (auto-accept)
          ↓ inline: openstation status X done
            ↓
            *→done (auto-commit)
              ↓ inline: claude -p commits changes
```

---

## 7. Failure Modes and Recovery

### 7.1 Verify Rejects (review → in-progress)

**Scenario**: The verify agent finds issues and transitions
`review → in-progress`.

**Behavior**: No autonomous hook fires on `*→in-progress`
(intentional — there's no auto-start hook for that transition).
The chain stops. The task stays in `in-progress` waiting for the
assignee agent to be re-dispatched.

**Recovery**: Manual intervention. The operator inspects the
rejection reason, optionally fixes issues, and either:
1. Re-runs the agent: `openstation run --task X --attached`
2. Or: the agent's session may still be active and can pick up
   the rework.

**Design decision**: We do NOT auto-restart on `*→in-progress`
because that would create a loop:
`review → in-progress → run → review → in-progress → ...`
The depth guard would eventually stop it, but burning through
retries without human review is wasteful. Rework is a signal
that human attention is needed.

### 7.2 Agent Crashes Mid-Task

**Scenario**: Agent process dies (OOM, network, Claude API
error) while task is `in-progress`.

**Behavior**: Task remains in `in-progress`. No hook fires
(no status transition happened). The tmux window may show the
error or may be gone.

**Recovery**: Manual. The operator checks the task status with
`openstation show X` and either:
1. Re-runs: `openstation run --task X --attached`
2. Suspends: `openstation status X ready` (triggers auto-start
   again)

### 7.3 Tmux Session Dies

**Scenario**: The tmux server crashes or the session is killed.

**Behavior**: All agent windows in that session are lost. Tasks
remain in their last persisted status.

**Recovery**: Same as agent crash — manual re-dispatch. Tasks
in `in-progress` can be re-run. Tasks in `ready` can be
re-promoted (but they're already ready, so re-running
`openstation run --task X` directly is simpler).

### 7.4 Multiple Subtasks Promoted to Ready Simultaneously

**Scenario**: Operator runs `openstation status X ready` for 3
subtasks in quick succession.

**Behavior**: Each promotion fires the `*→ready` auto-start
hook. Three `os-dispatch` calls create three tmux windows. Three
Claude agent sessions run in parallel.

**Risks**:
- Token burn — 3 parallel Claude sessions
- File conflicts — agents may edit the same files
- Race conditions on parent status

**Mitigation** (current): Documented risk. Users should promote
one subtask at a time. The depth guard prevents infinite
recursion but not parallel fan-out.

**Mitigation** (future, chain-next hook): The chain-next hook
dispatches only ONE subtask at a time, serializing execution
naturally. The parallel risk only exists with manual promotion.

### 7.5 Task Has No Assignee

**Scenario**: Task is promoted to `ready` but has no `assignee`
field.

**Behavior**: The auto-start hook checks for an assignee and
exits 0 (no-op) if none is set. `openstation run --task X` would
also fail because it needs an agent to load.

**Recovery**: Set the assignee (`openstation update X assignee:researcher`)
then promote again or re-dispatch.

### 7.6 Agent Spec Missing

**Scenario**: Task has `assignee: researcher` but no agent spec
exists at `agents/researcher.md`.

**Behavior**: `openstation run --task X` fails with an error.
The auto-start hook's `os-dispatch` spawns the window, but the
command inside it fails. The tmux window shows the error.

**Recovery**: Create the agent spec, then re-dispatch.

### 7.7 Auto-Accept Triggers Auto-Commit Failure

**Scenario**: Auto-accept runs `openstation status X done`, which
triggers auto-commit, which fails (e.g., git conflicts).

**Behavior**: Auto-commit is a post-hook. Its failure is a
warning only — the `done` transition is already persisted. The
task is `done` but uncommitted changes remain in the working
tree.

**Recovery**: Manual commit or re-run auto-commit.

---

## 8. Opt-In Mechanism

### 8.1 Decision: Project-Level Opt-In via Settings

Autonomous chaining is controlled by a project-level setting:

```json
{
  "autonomous": {
    "enabled": false
  }
}
```

**Default: `false`** (off). Users must explicitly enable it.

### 8.2 Why Project-Level

| Scope | Pros | Cons |
|-------|------|------|
| **Per-task** (frontmatter flag) | Fine-grained control | Noisy — must set on every task; easy to forget; clutters frontmatter |
| **Per-project** (settings) | Single switch; clear intent; easy to toggle | All-or-nothing for the project |
| **Always-on** | Zero config | Dangerous — surprise agent execution; no off switch |

**Chosen: Per-project.** It's the right granularity for a
power-user feature. Users who enable it understand the
implications. Per-task is overly granular for a feature that's
meant to be a workflow mode, not a per-task decision.

### 8.3 How It Works

Every autonomous hook script checks the setting at the top:

```bash
ENABLED=$(python3 -c "
import json, sys
try:
    data = json.load(open('${OS_VAULT_ROOT}/.openstation/settings.json'))
except Exception: data = {}
print(data.get('autonomous', {}).get('enabled', False))
" 2>/dev/null || echo "False")

if [[ "$ENABLED" != "True" ]]; then
  exit 0
fi
```

When disabled, hooks exit immediately with success — the
transition proceeds normally, but no autonomous dispatch happens.

### 8.4 Enabling

```bash
# Edit .openstation/settings.json
# Set "autonomous": { "enabled": true }
```

No CLI command for this yet. Direct file edit is sufficient for
a power-user feature. A future `openstation config` command could
provide a nicer UX.

### 8.5 Safety Properties

- **Off by default** — new installs and existing projects are
  unaffected
- **Hooks are always registered** in `settings.json` — but they
  no-op when `autonomous.enabled` is false
- **Disabling mid-chain** — if you set `enabled: false` while an
  agent is running, the current agent finishes normally. The next
  hook in the chain (e.g., `*→review`) will see `enabled: false`
  and stop. Clean shutdown with no orphaned state.

---

## 9. Summary of Files

### New Files

| File | Purpose |
|------|---------|
| `bin/os-dispatch` | Shared tmux dispatch helper |
| `bin/hooks/auto-start` | `*→ready` → dispatch agent run |
| `bin/hooks/auto-verify` | `*→review` → dispatch verify run |
| `bin/hooks/auto-accept` | `*→verified` → inline `status done` |

### Modified Files

| File | Change |
|------|--------|
| `settings.json` | Add 3 autonomous hooks + `autonomous` config |

### Unchanged Files

| File | Reason |
|------|--------|
| `src/openstation/hooks.py` | `_build_hook_env()` stays as-is |
| `bin/hooks/auto-commit` | Existing hook, no changes |
| `bin/hooks/suspend` | Existing hook, no changes |
