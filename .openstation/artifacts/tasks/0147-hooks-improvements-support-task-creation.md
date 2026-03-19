---
kind: task
name: 0147-hooks-improvements-support-task-creation
type: feature
status: backlog
assignee: architect
owner: user
created: 2026-03-17
subtasks:
  - "[[0148-spec-taskcreate-hook-category-design]]"
  - "[[0149-implement-taskcreate-hooks-in-cli]]"
---

# Hooks Improvements Support Task Creation Hooks

## Requirements

1. Add a new hook category `TaskCreate` that fires when a task is created via `openstation create`
2. Define the matcher format for creation hooks (e.g., by initial status, task type, or catch-all `*`)
3. Define environment variables passed to creation hooks (task name, status, type, assignee, task file path, vault root)
4. Determine timing: should hooks fire before or after the task file is written? (Pre-create hooks could abort creation; post-create hooks can read the file)
5. Integrate hook execution into `cmd_create()` in `tasks.py`
6. Add tests for creation hook matching, execution, and failure handling

## Context

The current hooks spec (`artifacts/specs/task-lifecycle-hooks.md` § 6) explicitly lists "Create-time hooks" as a deferred feature, noting: "Different trigger (no old status). Needs its own matcher design."

## Subtasks

1. **0148 — Spec** (architect) — Design `TaskCreate` matcher format, env vars, timing
2. **0149 — Implementation** (developer) — Implement in CLI, add tests, update docs

## Verification

- [ ] `TaskCreate` hook category is designed with matcher format
- [ ] Environment variables for creation hooks are defined
- [ ] Hook timing (pre/post create) is decided with rationale
- [ ] `openstation create` fires matching hooks
- [ ] Failed hooks abort or report errors appropriately
- [ ] Tests cover creation hook scenarios
