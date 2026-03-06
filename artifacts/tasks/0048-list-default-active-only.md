---
kind: task
name: 0048-list-default-active-only
status: done
assignee: developer
owner: manual
created: 2026-03-04
---

# List command: default to active tasks only

## Requirements

- Change `openstation list` default filter to show only `ready`
  and `in-progress` tasks (instead of all non-done/non-failed).
- `backlog` tasks should no longer appear in the default output.
- Explicit `--status backlog` or `--status all` must still work.
- Update `/openstation.list` command doc to reflect the new
  default behavior.

## Verification

- [x] `openstation list` (no flags) shows only ready and in-progress tasks
- [x] `openstation list --status backlog` shows backlog tasks
- [x] `openstation list --status all` shows all tasks
- [x] Existing tests updated to match new default
