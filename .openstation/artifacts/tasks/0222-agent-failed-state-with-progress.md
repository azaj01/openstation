---
kind: task
name: 0222-agent-failed-state-with-progress
type: feature
status: backlog
assignee:
owner: user
subtasks:
  - "[[0225-failed-status-spec-and-docs]]"
  - "[[0226-failed-status-cli-and-command]]"
created: 2026-03-23
---

# Agent Failed State with Mandatory Progress Report

## Context

When an agent cannot complete a task (e.g., max turns exhausted,
missing permissions, blocked by external dependency), there is no
formal way to record the failure. The agent should transition the
task to a `failed` status and log a descriptive progress entry
explaining why, so the supervisor can diagnose and fix the issue
before retrying.

Currently the lifecycle defines `rejected` (descoped/superseded)
but not `failed` (attempted but unable to complete). These are
semantically different: `rejected` means "we chose not to do
this", `failed` means "we tried and couldn't finish".

## Requirements

### 1. Add `failed` status to the lifecycle

Add `failed` as a terminal status in `docs/lifecycle.md`:

- Valid transition: `in-progress -> failed`
- Only the assignee (executing agent) may transition to `failed`
- Add to the Status Descriptions table:
  `failed` — Agent attempted but could not complete the task

### 2. Update task spec

Add `failed` to the Status Values table in `docs/task.spec.md`.

### 3. Enforce mandatory progress entry on failure

When an agent transitions a task to `failed`, it **must** append
a `## Progress` entry (via `/openstation.progress`) before or
as part of the transition. The progress entry must include:

- **Failure reason** — concrete, actionable description (not
  just "failed"). Examples:
  - "Max turns (100) exhausted while debugging flaky test in test_hooks.py"
  - "Missing write permission to /etc/systemd — needs root access"
  - "Blocked: upstream API returns 503, cannot test integration"
- **Work completed so far** — what was accomplished before failure
- **Suggested fix** — what the supervisor should do so the agent
  can retry successfully

### 4. CLI support

Update `openstation status` to accept `failed` as a valid target
status from `in-progress`. Validate that the task has a progress
entry with failure context (or accept a `--reason` flag that
appends one automatically).

### 5. Create `/openstation.fail` command

Create a slash command that combines the status transition and
progress entry into a single action:

```
/openstation.fail <task> "<reason>"
```

This should:
1. Validate task is `in-progress`
2. Append a progress entry with the failure reason
3. Transition status to `failed`

### 6. Recovery path

Define `failed -> ready` as a valid transition (allows retry
after the supervisor fixes the blocking issue). The supervisor
should update requirements or context before moving back to
`ready`.

### 7. Update CLAUDE.md

The lifecycle summary in CLAUDE.md already mentions `failed` —
verify it stays consistent with the updated lifecycle.

## Subtasks

### HIGH Priority

1. **0223 — Spec & docs** — Add `failed` status to `lifecycle.md`,
   `task.spec.md`, and verify `CLAUDE.md` consistency. Assignee: author.

2. **0224 — CLI & command** — Implement `openstation status` support
   for `failed`, create `/openstation.fail` command, add tests.
   Depends on 0223. Assignee: developer.

## Verification

- [ ] `failed` status exists in `docs/lifecycle.md` with transitions `in-progress -> failed` and `failed -> ready`
- [ ] `failed` status exists in `docs/task.spec.md` Status Values table
- [ ] `/openstation.fail` command exists and transitions + logs progress in one step
- [ ] `openstation status <task> failed` works from `in-progress`
- [ ] Progress entry is mandatory — failing without a reason is rejected
- [ ] Progress entry includes failure reason, work completed, and suggested fix
- [ ] `failed -> ready` transition works for retry after fix
- [ ] Tests cover: transition to failed, mandatory reason, recovery to ready
