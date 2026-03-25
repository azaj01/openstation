---
kind: task
name: 0225-failed-status-spec-and-docs
type: documentation
status: ready
assignee: author
owner: user
parent: "[[0222-agent-failed-state-with-progress]]"
created: 2026-03-23
---

# Add Failed Status to Lifecycle and Task Spec

## Context

Parent task [[0222-agent-failed-state-with-progress]] introduces
a `failed` status for when agents cannot complete a task. This
subtask lands the spec and doc changes that define the status,
its transitions, and its semantics. The implementation subtask
(0226) depends on these definitions.

## Requirements

### 1. Update `docs/lifecycle.md`

Add `failed` as a status with these transitions:

```
in-progress -> failed     (agent cannot complete — must log reason)
failed -> ready           (supervisor fixes issue, retries)
```

Add to the Status Descriptions table:

| Status | Meaning |
|--------|---------|
| `failed` | Agent attempted but could not complete the task |

Add a guardrail: transitioning to `failed` requires a
`## Progress` entry explaining the failure. The entry must
include failure reason, work completed so far, and suggested
fix. Reference `/openstation.fail` as the dedicated command.

Add ownership note: only the assignee (executing agent) may
transition to `failed`. The supervisor uses `failed -> ready`
to retry.

### 2. Update `docs/task.spec.md`

Add `failed` to the Status Values table:

| Value | Meaning |
|-------|---------|
| `failed` | Agent attempted but could not complete the task |

### 3. Verify CLAUDE.md consistency

The lifecycle summary in `CLAUDE.md` already mentions `failed`.
Confirm the status list and transition summary remain consistent
with the updated lifecycle. Fix if needed.

## Verification

- [ ] `docs/lifecycle.md` has `in-progress -> failed` and `failed -> ready` transitions
- [ ] `docs/lifecycle.md` Status Descriptions table includes `failed`
- [ ] `docs/lifecycle.md` guardrail section requires progress entry with reason on failure
- [ ] `docs/task.spec.md` Status Values table includes `failed`
- [ ] `CLAUDE.md` lifecycle summary is consistent with the updated lifecycle
