---
kind: task
name: 0207-research-nested-claude-instance-limitation
type: research
status: done
assignee: researcher
owner: user
parent: "[[0204-hook-based-autonomous-task-chaining]]"
artifacts:
  - "[[artifacts/research/nested-claude-instance-limitation]]"
created: 2026-03-22
---

# Research Nested Claude Instance Limitation And Workarounds

## Requirements

Investigate why Claude Code cannot spawn nested `claude` processes
and identify viable workarounds. This is the primary blocker for
hook-based autonomous task chaining (0204).

### Questions to answer

1. **What exactly fails?** Run `claude -p "..."` from inside a
   claude session (via a hook or Bash tool). Capture the error
   message, exit code, and behavior.

2. **What causes the limitation?** Is it:
   - An environment variable guard (`CLAUDECODE`)?
   - A socket/lock conflict?
   - A process tree detection?
   - An intentional design constraint?

3. **Workarounds** — evaluate feasibility of each:
   - Unsetting/overriding env vars before spawning
   - `nohup`/`disown`/`setsid` to detach from parent process
   - Tmux: launch claude in a new pane/window from the hook
   - Queue-based: hook writes a job file, external watcher picks it up
   - Background daemon: long-running process polls for work
   - Claude Code SDK/sub-agent API (if any exists or is planned)

4. **Which workarounds preserve the hook model?** Hooks are
   synchronous — the cleanest solution lets the hook return
   immediately while the new claude session runs independently.

### Scope

- Focus on practical workarounds available today
- Test each approach that seems viable
- Document trade-offs (reliability, complexity, latency)

## Findings

### Root Cause

The limitation is an **environment variable guard**. Claude Code sets
`CLAUDECODE=1` on startup; child processes inherit it; the CLI refuses
to launch when the variable is present. The error message explicitly
says: *"To bypass this check, unset the CLAUDECODE environment variable."*

This is intentional — Anthropic states nested sessions would share
runtime resources (lock files, sockets, session state) and crash.

In Open Station, `hooks.py:_build_hook_env()` calls `os.environ.copy()`,
propagating `CLAUDECODE=1` to all hook subprocesses.

### Workarounds Evaluated (6 total)

| # | Approach | Viable | Returns Immediately | Complexity |
|---|----------|:------:|:-------------------:|:----------:|
| 1 | **Tmux** — `tmux new-window -e "CLAUDECODE="` | ✅ | ✅ | Low |
| 2 | **nohup/env -u** — `(env -u CLAUDECODE nohup ... &)` | ✅ | ✅ | Low |
| 3 | **Queue/watcher** — file + polling loop | ✅ | ✅ | Medium |
| 4 | **launchd WatchPaths** | ❌ | ✅ | Medium |
| 5 | **Claude Agent SDK** with env override | ⚠️ | ❌ | Medium |
| 6 | **Subagents / Agent Teams** | ❌ | N/A | N/A |

### Recommendation

**Tmux as primary, nohup as fallback.** The hook detects tmux
availability and dispatches accordingly:

```
tmux available? → tmux new-window -e "CLAUDECODE=" "openstation run ..."
tmux absent?    → (env -u CLAUDECODE nohup openstation run ... > /tmp/log 2>&1 &)
```

Tmux wins on simplicity, observability, and reliability. It returns
immediately, clears the env var cleanly via `-e`, and spawned sessions
are visible/attachable for debugging.

For production hardening later, upgrade to queue-based (approach 3)
for retry logic and guaranteed delivery.

Full analysis with concrete commands: [[artifacts/research/nested-claude-instance-limitation]]

## Progress

### 2026-03-22 — researcher

Completed research: identified CLAUDECODE=1 env var guard as root cause, evaluated 6 workarounds (tmux, nohup, queue, launchd, SDK, subagents), recommended tmux as primary approach for 0204. Produced research artifact at artifacts/research/nested-claude-instance-limitation.md.

## Downstream

- **`_build_hook_env()` change (optional)**: Consider stripping
  `CLAUDECODE` from the env dict passed to hooks, so hook scripts
  don't need to handle it themselves. Trade-off: some hooks may
  legitimately want to know they're inside a Claude session.
- **Loop prevention**: The hook-based chaining design needs a
  depth guard (e.g., `OS_HOOK_DEPTH`) to prevent infinite recursion
  when a hook triggers a transition that triggers the same hook.
- **Claude Agent SDK PR #594**: Once merged, the SDK will auto-strip
  `CLAUDECODE` from subprocess environments. This could enable a
  cleaner programmatic approach in the future.

## Verification

- [ ] Root cause of nested claude limitation identified and documented
- [ ] At least 3 workarounds evaluated with pros/cons
- [ ] At least 1 workaround demonstrated working (or all proven infeasible with evidence)
- [ ] Findings recorded in ## Findings section
- [ ] Recommendation for which approach to use in 0204
