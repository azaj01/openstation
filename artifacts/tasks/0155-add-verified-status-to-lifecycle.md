---
kind: task
name: 0155-add-verified-status-to-lifecycle
type: feature
status: done
assignee:
owner: user
subtasks:
  - "[[0156-docs-add-verified-status]]"
  - "[[0157-cli-verified-status-transitions]]"
  - "[[0158-commands-update-verify-done-flow]]"
created: 2026-03-17
---

# Add `verified` Status to Lifecycle

## Context

Tasks in `review` have no visible distinction between "awaiting
verification" and "all checks passed, awaiting owner sign-off."
`openstation list --status review` shows both equally — the owner
can't tell which tasks need verification vs. which are ready to
accept.

## Requirements

Add `verified` as a new status between `review` and `done`.

### State machine change

```
review → verified       (/openstation.verify — all checks pass)
verified → done         (/openstation.done — owner accepts)
verified → failed       (/openstation.reject — owner rejects after re-review)
review → failed         (existing — owner rejects before/during verification)
failed → in-progress    (existing — agent reworks)
```

### What changes

1. **`docs/lifecycle.md`** — add `verified` to the transition
   diagram and status descriptions. `verified` means "all
   verification items passed, awaiting owner sign-off."

2. **`docs/task.spec.md`** — add `verified` to the Status Values
   table. Description: "All verification checks passed, awaiting
   owner acceptance."

3. **CLI `openstation status`** — allow `review → verified` and
   `verified → done` / `verified → failed` transitions.

4. **`/openstation.verify`** — when all items pass, transition
   status from `review` to `verified` (instead of asking to run
   `/openstation.done`). When any item fails, stay in `review`.

5. **`/openstation.done`** — accept tasks in `verified` status
   (not `review`). If task is in `review`, tell the user to run
   verification first.

6. **`openstation list`** — `--status verified` works as a
   filter. Existing `--status review` no longer includes verified
   tasks.

7. **Sub-task rules** — `verified` ranks between `review` and
   `done` for parent auto-promotion. A verified sub-task does not
   auto-promote the parent beyond `in-progress`.

8. **`openstation run --verify`** — no change needed (it already
   dispatches `/openstation.verify`).

### What does NOT change

- The `done` status still means "owner accepted." Its meaning is
  unchanged.
- The `failed` status and rework loop are unchanged.
- Artifact promotion still happens at `done`, not `verified`.

## Verification

- [ ] `verified` appears in lifecycle.md transition diagram
- [ ] `verified` appears in task.spec.md Status Values table
- [ ] `openstation status <task> verified` works from `review`
- [ ] `openstation status <task> done` works from `verified`
- [ ] `openstation status <task> done` rejects tasks in `review`
- [ ] `/openstation.verify` transitions to `verified` on all-pass
- [ ] `/openstation.done` requires `verified` status
- [ ] `openstation list --status verified` filters correctly
- [ ] Sub-task parent auto-promotion handles `verified` correctly
- [ ] Existing tests updated, new transition tests added
