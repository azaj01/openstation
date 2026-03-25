---
kind: task
name: 0204-hook-based-autonomous-task-chaining
type: feature
status: in-progress
assignee: 
owner: user
created: 2026-03-22
subtasks:
  - "[[0207-research-nested-claude-instance-limitation]]"
  - "[[0208-spec-hook-based-autonomous-chaining]]"
  - "[[0209-implement-autonomous-chaining-hooks-and]]"
---

# Hook-Based Autonomous Task Chaining

## Requirements

Wire post-transition hooks so that promoting a task to `ready`
triggers fully autonomous execution through the entire lifecycle:

```
MANUAL              AUTO            AUTO           AUTO            AUTO           AUTO
backlog → ready → in-progress → review → verified → done → (next subtask)
            ↑         ↑              ↑         ↑         ↑         ↑
          triage    hook:run      agent     hook:verify hook:done hook:chain
```

Four post-hooks:

| Hook | Trigger | Action |
|------|---------|--------|
| Auto-start | `*→ready` | `openstation run --task $OS_TASK_NAME` |
| Auto-verify | `*→review` | `openstation run --task $OS_TASK_NAME --verify` |
| Auto-accept | `*→verified` | `openstation status $OS_TASK_NAME done` |
| Chain-next | `*→done` | Find parent, run next ready subtask |

The only human touchpoint is promoting a task to `ready`.
Everything after that is autonomous.

### Blocker: nested Claude instances

Hooks run as subprocesses of `openstation status`, which itself
runs inside a Claude agent session. Claude Code cannot spawn
nested `claude` processes. This blocks three of the four hooks:

- `*→ready` → `openstation run` — needs claude
- `*→review` → `openstation run --verify` — needs claude
- `*→done` → chain next subtask — needs claude

Only `*→verified` → `openstation status done` works today
(pure CLI, no claude needed).

**Possible workarounds** (to investigate once the nested-claude
limitation is resolved or worked around):

- Queue-based: hook writes to a file/queue, an external watcher picks it up
- Tmux-based: hook launches claude in a new tmux pane
- Signal-based: hook signals a parent orchestrator to spawn the next run

This feature is **blocked until nested claude invocation is
resolved** — either by Claude Code itself or via a workaround.

### Edge cases to address

- Loop prevention (hook triggers transition → triggers hook)
- Verify rejection → `review → in-progress` rework cycle
- Subtask-only vs standalone task behavior
- Hook timeout for long-running agent executions
- Detached execution — hooks are synchronous but agent runs take minutes

## Verification

- [x] `*→ready` hook auto-starts task execution
- [x] `*→review` hook auto-launches verification
- [ ] `*→verified` hook auto-transitions to done
- [ ] `*→done` hook chains to next ready subtask in parent
- [ ] Full chain works end-to-end: promote to ready → autonomous through done
- [x] Loop prevention tested (no infinite hook recursion)
- [ ] Verify rejection triggers rework without breaking the chain
- [ ] Works for both standalone tasks and subtask trees

## Verification Report

*Verified: 2026-03-24*

| # | Criterion | Result | Evidence |
|---|-----------|--------|----------|
| 1 | `*→ready` hook auto-starts task execution | PASS | `bin/hooks/auto-start` exists (+x), registered in settings.json as `*→ready` post-hook, dispatches via `os-dispatch` with `--no-attach`, tests in `TestAutoStart` (7 tests) |
| 2 | `*→review` hook auto-launches verification | PASS | `bin/hooks/auto-verify` exists (+x), registered in settings.json as `*→review` post-hook, dispatches with `--verify`, tests in `TestAutoVerify` (3 tests) |
| 3 | `*→verified` hook auto-transitions to done | FAIL | `bin/hooks/auto-accept` script exists and works correctly (calls `openstation status done`), BUT **not registered** in settings.json — no `*→verified` matcher. Hook would never fire. Also `autonomous.enabled` is `true` in settings.json but test `test_autonomous_section_exists` asserts `False`. |
| 4 | `*→done` hook chains to next ready subtask | FAIL | No chain-next script in `bin/hooks/`. No `*→done` chaining hook in settings.json (only `auto-commit`). Grep confirms no implementation exists. |
| 5 | Full chain end-to-end | FAIL | Breaks at `verified→done` (auto-accept not wired) and `done→next` (no chain-next). Cannot complete ready→done autonomously. |
| 6 | Loop prevention tested | PASS | `OS_HOOK_DEPTH` guard in all 3 hooks. Tests: `test_noop_when_depth_exceeds_max` for all hooks, `test_noop_at_exact_max_depth` for auto-start. Max depth default 5. |
| 7 | Verify rejection triggers rework | FAIL | No test for review→in-progress→review cycle. No evidence this edge case was verified. |
| 8 | Works for standalone and subtask trees | FAIL | No chain-next means subtask trees don't chain. No tests differentiate standalone vs subtask behavior. |

### Summary

3 passed, 5 failed. The auto-start, auto-verify hooks and loop prevention are solid. The auto-accept hook exists but isn't wired in settings.json, chain-next is unimplemented, and edge-case scenarios lack coverage.

### What Needs Fixing

- **Register auto-accept hook**: Add `{"matcher": "*→verified", "command": "bin/hooks/auto-accept", "phase": "post", "timeout": 30}` to settings.json
- **Fix `autonomous.enabled` default**: Settings.json has `true` but test expects `false` — one of them is wrong
- **Implement chain-next hook** (`*→done`): Script to find parent, identify next ready subtask, dispatch it — or descope from verification criteria
- **Add rework cycle test**: Verify review→in-progress doesn't loop and re-entering review re-fires auto-verify
- **Add standalone vs subtask test**: Confirm hooks work for both task types
