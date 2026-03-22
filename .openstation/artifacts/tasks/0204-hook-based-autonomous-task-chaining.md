---
kind: task
name: 0204-hook-based-autonomous-task-chaining
type: feature
status: review
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

- [ ] `*→ready` hook auto-starts task execution
- [ ] `*→review` hook auto-launches verification
- [ ] `*→verified` hook auto-transitions to done
- [ ] `*→done` hook chains to next ready subtask in parent
- [ ] Full chain works end-to-end: promote to ready → autonomous through done
- [ ] Loop prevention tested (no infinite hook recursion)
- [ ] Verify rejection triggers rework without breaking the chain
- [ ] Works for both standalone tasks and subtask trees
