---
kind: task
name: 0088-subtasks-inherit-parent-status-by
status: done
assignee: developer
owner: user
created: 2026-03-09
---

# Subtasks inherit parent status by default

Two related lifecycle rules for parent/subtask consistency.

## Requirements

### Rule 1: Status inheritance on create

When creating a subtask with `--parent` and no explicit
`--status`, the subtask inherits the parent's status (if
`backlog` or `ready`). Currently always defaults to `backlog`.

### Rule 2: Auto-promote parent (already implemented)

When a subtask transitions to a status that outranks its parent,
the parent is auto-promoted. This is already in the CLI.

### Changes needed

1. **`docs/lifecycle.md`** — add both rules to the spec:
   - Subtask status inheritance on create
   - Parent auto-promotion on subtask transition
2. **`bin/openstation` `cmd_create`** — read parent status when
   `--parent` provided and no `--status`, use it as default
3. **Tests** for the new inheritance behavior

## Verification

- [ ] `docs/lifecycle.md` documents status inheritance rule
- [ ] `docs/lifecycle.md` documents parent auto-promotion rule
- [ ] `create --parent X` inherits parent's status when no
      `--status` given
- [ ] Explicit `--status` overrides inheritance
- [ ] Tests pass
