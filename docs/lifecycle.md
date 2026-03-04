---
kind: workflow
name: task-lifecycle
---

# Task Lifecycle

Authoritative reference for how tasks move through the system.
Skills and agents reference this file — it is the single
source of truth for lifecycle rules.

For task format, field schema, and naming conventions see
`docs/task.spec.md`.

## Status Transitions

```
backlog → ready          (use /openstation.ready)
ready → in-progress      (assigned agent picks up the task)
in-progress → review     (agent finishes work)
review → done            (owner verifies — use /openstation.done)
review → failed          (owner rejects — use /openstation.reject)
failed → in-progress     (agent reworks)
```

### Guardrails

- Each user-driven transition has a dedicated command.
  `/openstation.update` does not change status — it only edits
  metadata fields (agent, owner, parent, etc.).
- `backlog → ready` is only allowed via `/openstation.ready`,
  which validates requirements and updates the status.
- `review → done` is only allowed via `/openstation.done`, which
  completes the task in one step.
- `review → failed` is only allowed via `/openstation.reject`,
  which records the rejection reason and marks the task failed.
- Agents must NOT self-verify their own work. After completing
  requirements, set `status: review` and stop. Only the
  designated `owner` may transition to `done` or `failed`.

## Ownership

The `owner` field names who is responsible for verification.

- Value is an agent name or `user` (default).
- Only the designated owner may transition a task from `review` →
  `done` or `review` → `failed`.
- When `owner: user`, a human operator verifies.

## Sub-Tasks

A task may be decomposed into sub-tasks. Sub-tasks are full
tasks with their own canonical folder in `artifacts/tasks/`,
discovered through their parent rather than independently.
See `docs/storage-query-layer.md` § 4 for the full
sub-task storage model (creation procedure, symlink conventions).

### Blocking Rule

All sub-tasks must reach `done` before the parent can proceed
to `review`.

### Lifecycle

Sub-tasks follow the same status transitions as any other task.
Their status is tracked in their own `index.md` frontmatter.

## Artifact Storage

Artifacts are outputs produced during task execution. They are
stored permanently in `artifacts/<category>/` and never move.
See `docs/storage-query-layer.md` §§ 1, 3 for the
canonical storage model, category directories, and routing table.

## Artifact Promotion

When a task passes verification, `/openstation.done` sets
`status: done` in frontmatter. Artifacts are already in
`artifacts/` and do not need to be moved.

Discovery symlinks (e.g. `agents/<name>.md`) are created by
`/openstation.done` after verification — never during task
execution. See `docs/storage-query-layer.md` § 2b
for the discovery symlink model.
