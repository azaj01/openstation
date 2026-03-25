---
kind: task
name: 0226-failed-status-cli-and-command
type: implementation
status: backlog
assignee: developer
owner: user
parent: "[[0222-agent-failed-state-with-progress]]"
created: 2026-03-23
---

# Implement Failed Status CLI Support and /openstation.fail Command

## Context

Parent task [[0222-agent-failed-state-with-progress]] introduces
a `failed` status. The spec and doc changes land in
[[0225-failed-status-spec-and-docs]] first. This subtask
implements the CLI and command support.

Depends on: 0225 (spec must be landed so the implementation
matches the defined transitions and semantics).

## Requirements

### 1. CLI `openstation status` support

Update `openstation status` to accept `failed` as a valid target
from `in-progress`:

- Add `in-progress -> failed` to the valid transitions
- Add `failed -> ready` to the valid transitions (recovery)
- When transitioning to `failed`, validate that the task file
  contains a `## Progress` entry with failure context. If no
  progress entry exists, reject the transition with an error:
  ```
  error: cannot transition to failed without a progress entry — use /openstation.fail or log progress first
  ```
- Alternatively, accept a `--reason` flag on `openstation status`
  that appends a progress entry automatically before transitioning

### 2. Create `/openstation.fail` slash command

Create `.openstation/commands/openstation.fail.md` that combines
progress logging and status transition:

```
/openstation.fail <task> "<reason>"
```

Procedure:
1. Parse task name and reason from arguments
2. Validate task is `in-progress` — error if not
3. Append a `## Progress` entry with:
   - Failure reason (from the argument)
   - Prompt agent to include work completed and suggested fix
4. Transition status to `failed` via `openstation status`

### 3. Tests

- Transition `in-progress -> failed` succeeds with progress entry
- Transition `in-progress -> failed` rejected without progress entry
- Transition `failed -> ready` succeeds (recovery path)
- `--reason` flag appends progress and transitions in one step
- Invalid transitions to `failed` from other statuses are rejected

## Verification

- [ ] `openstation status <task> failed` works from `in-progress`
- [ ] Transition to `failed` without progress entry is rejected with clear error
- [ ] `--reason` flag appends progress entry and transitions in one step
- [ ] `/openstation.fail` command file exists and follows command conventions
- [ ] `failed -> ready` transition works for retry
- [ ] Tests cover all cases: happy path, missing reason, recovery, invalid source status
