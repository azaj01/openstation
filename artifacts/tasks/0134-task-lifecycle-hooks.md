---
kind: task
name: 0134-task-lifecycle-hooks
type: feature
status: in-progress
assignee: architect
owner: user
created: 2026-03-14
subtasks:
  - "[[0135-hooks-spec-design-configuration-schema]]"
  - "[[0136-hooks-implementation-implement-hooks-in]]"
  - "[[0142-document-hooks-configuration-and-usage]]"
  - "[[0144-post-transition-hooks]]"
  - "[[0147-hooks-improvements-support-task-creation]]"
---

# Task Lifecycle Hooks

## Requirements

1. Users can define hooks that run commands on task status transitions (e.g., `ready→in-progress`, `in-progress→review`, `→done`)
2. Hook configuration lives in a settings file (e.g., `.openstation/settings.json` or similar), modeled after Claude Code's hook format
3. Each hook specifies: a `matcher` (status transition pattern), a `command` to execute, and an optional `timeout`
4. Hooks fire automatically when `openstation status` changes a task's status (CLI-driven transitions)
5. Hook commands receive context via environment variables (task name, old status, new status, task file path)
6. Hook execution is synchronous — if a hook fails (non-zero exit), the status transition is aborted and an error is reported
7. Multiple hooks can match the same transition; they run in declaration order

## Verification

- [ ] Hook configuration schema is defined and documented
- [ ] `openstation status` fires matching hooks on transitions
- [ ] Hook commands receive task context (name, old/new status, path) as env vars
- [ ] Failed hooks abort the status transition with a clear error message
- [ ] Multiple hooks for the same transition run in order
- [ ] Hooks with no matching transition are silently skipped
- [ ] Timeout enforcement works (kills long-running hooks)

## Subtasks

- `0135-hooks-spec` — Design hook configuration schema, execution model, and CLI integration points
- `0136-hooks-implementation` — Implement hooks in the CLI based on the spec
