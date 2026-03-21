---
kind: research
name: nested-claude-instance-limitation
agent: researcher
task: "[[0207-research-nested-claude-instance-limitation]]"
created: 2026-03-22
---

# Nested Claude Instance Limitation — Research

## Root Cause

**Confirmed: environment variable guard.** When Claude Code starts, it
sets `CLAUDECODE=1` in its process environment. Any child process
spawned via the Bash tool inherits this variable. On startup, the
`claude` CLI checks for `CLAUDECODE` and refuses to launch:

```
Error: Claude Code cannot be launched inside another Claude Code session.
Nested sessions share runtime resources and will crash all active sessions.
To bypass this check, unset the CLAUDECODE environment variable.
```

This is an **intentional design constraint** — not a bug. Anthropic's
rationale: nested sessions would share runtime resources (lock files,
sockets, `~/.claude/` session state, token accounting) and could crash
all active sessions.

A secondary variable `CLAUDE_CODE_ENTRYPOINT` (values: `"cli"`,
`"sdk-py"`) also propagates to children but is informational, not a
guard.

### Propagation in Open Station hooks

`hooks.py:_build_hook_env()` calls `os.environ.copy()`, which
propagates `CLAUDECODE=1` to all hook subprocesses. This is the
direct mechanism that blocks `openstation run` (which spawns
`claude`) from within a hook.

## Workarounds Evaluated

### 1. Tmux — launch in a new window ✅ RECOMMENDED

The hook runs `tmux new-window` to spawn Claude in a separate tmux
window with `CLAUDECODE` cleared via the `-e` flag.

```bash
#!/usr/bin/env bash
tmux new-window -n "os-$OS_TASK_NAME" \
  -e "CLAUDECODE=" \
  "openstation run --task $OS_TASK_NAME --attached"
```

| Criterion | Assessment |
|-----------|-----------|
| Bypasses guard | Yes — `-e "CLAUDECODE="` clears the var |
| Returns immediately | Yes — `tmux new-window` is non-blocking |
| Complexity | Low — single command |
| Reliability | High — tmux client-server model is battle-tested |
| Observability | High — session visible in tmux, attachable |
| Dependencies | tmux must be running |

**Verdict**: Best balance of simplicity, reliability, and visibility.
Guard with `tmux info >/dev/null 2>&1` to fail gracefully when tmux
is not available.

### 2. nohup/env -u — background detach ⚠️ FALLBACK

Spawn Claude in a subshell with the env var stripped and
backgrounded.

```bash
#!/usr/bin/env bash
(env -u CLAUDECODE nohup openstation run --task "$OS_TASK_NAME" \
  > "/tmp/os-$OS_TASK_NAME.log" 2>&1 &)
```

| Criterion | Assessment |
|-----------|-----------|
| Bypasses guard | Yes — `env -u` removes the variable |
| Returns immediately | Yes — subshell + `&` returns instantly |
| Complexity | Low — no dependencies |
| Reliability | Medium — fragile around fd inheritance, signals |
| Observability | Low — output only in log file |
| Dependencies | None |

**Caveat**: `setsid` is not available on macOS. The `(... &)` subshell
pattern is sufficient for detachment in practice but less robust than
a full session leader. Stdout/stderr *must* be redirected to avoid
blocking the parent pipe.

### 3. Queue-based — file watcher ⚠️ PRODUCTION OPTION

Hook writes a JSON job file; an external watcher spawns Claude.

```bash
# Hook writes:
cat > "$QUEUE_DIR/$(date +%s)-$OS_TASK_NAME.json" <<EOF
{"task": "$OS_TASK_NAME", "action": "run"}
EOF

# Watcher loop (separate process):
while true; do
  for f in "$QUEUE_DIR"/*.json; do
    [ -f "$f" ] || continue
    task=$(jq -r .task "$f")
    env -u CLAUDECODE openstation run --task "$task" &
    mv "$f" "$f.done"
  done
  sleep 2
done
```

| Criterion | Assessment |
|-----------|-----------|
| Bypasses guard | Yes — watcher has clean environment |
| Returns immediately | Yes — file write is instant |
| Complexity | Medium — requires watcher lifecycle management |
| Reliability | High — clean decoupling, retryable |
| Observability | Medium — depends on watcher logging |
| Dependencies | Watcher process must be running |

**Verdict**: Best for guaranteed delivery with retry logic, but
overkill for the current iteration. Good upgrade path.

### 4. launchd WatchPaths ❌ NOT RECOMMENDED

macOS LaunchAgent watches a directory and runs a script on change.

| Criterion | Assessment |
|-----------|-----------|
| Bypasses guard | Yes — launchd starts with clean env |
| Returns immediately | Yes |
| Complexity | Medium — plist with absolute paths |
| Reliability | **Low** — Apple documents WatchPaths as race-prone |
| Dependencies | plist installation, user-specific paths |

**Verdict**: Race-prone mechanism, hard to debug, brittle paths.

### 5. Claude Agent SDK with env override ⚠️ FUTURE OPTION

```python
from claude_agent_sdk import query, ClaudeAgentOptions
options = ClaudeAgentOptions(env={"CLAUDECODE": ""})
async for msg in query(prompt="...", options=options):
    ...
```

| Criterion | Assessment |
|-----------|-----------|
| Bypasses guard | Yes — env override strips the var |
| Returns immediately | No — SDK is synchronous streaming |
| Complexity | Medium — requires Python async, SDK dependency |
| Reliability | Medium — workaround; official fix pending (PR #594) |
| Dependencies | `claude-agent-sdk` package |

**Verdict**: Would require wrapping in a background process to be
non-blocking. Interesting once PR #594 lands, but adds a heavy
dependency.

### 6. Subagents / Agent Teams ❌ NOT SUITABLE

- **Subagents** run within the current session — cannot spawn other
  subagents (architectural constraint). Cannot create independent
  sessions for task chaining.
- **Agent Teams** (experimental, `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`)
  spawn independent sessions but teammates cannot spawn their own
  teams. Single level only, and experimental.

Neither supports the arbitrary chaining needed for
`ready → run → review → verify → done → next`.

## Simple vs Queue/Service — Deep Comparison

### How they differ

**Simple (tmux/nohup)**: Hook directly spawns `claude` in a detached
process. Fire-and-forget — no intermediary.

**Queue/Service**: Hook writes a job file. A separate long-running
process picks it up and spawns `claude`. Two-phase — write then
execute.

### Trade-off matrix

| Dimension | tmux/nohup | Queue/Service |
|-----------|-----------|---------------|
| Setup | Zero — tmux already running | Must start + supervise a watcher |
| Latency | ~instant (fork + exec) | 1-2s polling delay (or ~instant with fswatch) |
| Reliability | Fire-and-forget — spawn failure = lost | Retry failed jobs, `.failed/` directory |
| Observability | tmux: visible pane; nohup: log only | Central log, job status files on disk |
| Concurrency control | None — N hooks = N parallel sessions | Watcher can serialize or cap concurrency |
| Crash recovery | Lost — no record of intent | Jobs persist on disk — restart watcher, resume |
| Ordering | None — race between hooks | FIFO by timestamp in filename |
| Dependencies | tmux (already present) | Watcher process + optional fswatch |
| Code size | ~5 lines (hook script) | ~30-50 lines (hook + watcher + job format) |

### What the queue model enables long-term

1. **Rate limiting** — process 1 task at a time, queue the rest.
   Prevents token burn from parallel sessions.
2. **Priority** — sort jobs by priority field, not just arrival time.
3. **Retry with backoff** — if claude crashes or verification fails,
   re-queue with a delay.
4. **Audit trail** — `.done/` and `.failed/` directories give complete
   history of what ran and when.
5. **Multi-machine** — queue directory could be a shared mount or
   synced folder. Watcher doesn't need to be co-located.
6. **Pause/resume** — stop the watcher to pause all autonomous
   execution; restart to resume. No hook changes needed.
7. **Pluggable backends** — start with filesystem polling, swap to
   Redis/SQLite/SQS later without changing hook scripts.
8. **Dead letter queue** — jobs failing N times get moved aside for
   human review.

### What tmux/nohup can't easily do

- **No memory of intent** — if the process dies mid-spawn, the task
  is stranded in the wrong status with no record of what should have
  happened.
- **No concurrency control** — 5 subtasks promoted to `ready`
  simultaneously = 5 parallel claude sessions competing for tokens.
- **No retry** — a transient failure (network, rate limit) means
  manual intervention.

### Decision

**Start with tmux. Migrate to queue when a pain point is hit.** The
hook script interface is the same either way (spawn a process vs write
a file), so migrating is a small diff — not a redesign. The queue
becomes worth it when chaining subtask trees with 3+ parallel
branches, running unattended, or needing concurrency control.

## Recommendation for 0204

**Use tmux as the primary mechanism with nohup as fallback.**

```
Hook fires → tmux available?
  YES → tmux new-window -e "CLAUDECODE=" "openstation run --task ..."
  NO  → (env -u CLAUDECODE nohup openstation run --task ... > /tmp/log 2>&1 &)
```

### Why tmux

1. **Returns immediately** — hooks stay synchronous with zero latency
2. **Clean env** — `-e "CLAUDECODE="` is explicit and reliable
3. **Observable** — spawned sessions visible in tmux panes
4. **No new dependencies** — tmux is already available on this system
5. **Natural fit** — agents already run in tmux sessions

### Implementation changes needed

1. **Hook scripts**: Use the tmux/nohup pattern above
2. **`_build_hook_env()` (optional)**: Strip `CLAUDECODE` from the
   env dict so hook scripts don't need to handle it themselves
3. **Loop prevention**: Set `OS_HOOK_DEPTH=1` or similar in the
   spawned session's env to prevent infinite hook recursion

### Future upgrade path

If reliability requirements grow (retry, guaranteed delivery, audit
log), migrate to the queue-based approach. The tmux mechanism is
sufficient for the initial implementation.

## Sources

- GitHub issue #25434: Session docs missing nested-Claude launch guard
- GitHub issue #573: Subprocess inherits CLAUDECODE=1 preventing SDK usage
- GitHub issue #25803: Nested session check blocks non-interactive subcommands
- GitHub issue #29543: `claude --print` no output when CLAUDECODE unset inside session
- GitHub issue #4182: Sub-Agent Task Tool not exposed for nested agents
- Claude Code Environment Variables documentation
- Claude Code Sub-agents documentation
- Claude Code Agent Teams documentation
- Claude Agent SDK Python repository (PR #594)
