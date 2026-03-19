---
kind: task
name: 0105-add-backward-transitions-to-task
type: implementation
status: done
assignee: developer
owner: user
created: 2026-03-10
---

# Add backward transitions to task lifecycle

Add `ready → backlog` as a valid transition in the task lifecycle. Currently the lifecycle only allows forward movement, but deprioritizing a task is a legitimate action.

## Requirements

1. Add `ready → backlog` to `VALID_TRANSITIONS` in `src/openstation/core.py`
2. Update `docs/lifecycle.md` to document the backward transition and when it's appropriate (e.g., deprioritization, requirements changed, blocked by other work)
3. Verify `openstation status <task> backlog` works for tasks in `ready`

## Verification

- [x] `openstation status <task> backlog` succeeds when task is `ready`
- [x] `VALID_TRANSITIONS` includes `ready → backlog`
- [x] `docs/lifecycle.md` documents the backward transition
- [x] Existing forward transitions still work
- [x] Existing tests pass (191 passed)
