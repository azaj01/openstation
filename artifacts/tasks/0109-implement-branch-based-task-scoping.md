---
kind: task
name: 0109-implement-branch-based-task-scoping
type: implementation
status: backlog
assignee: developer
owner: user
parent: "[[0122-worktree-integration]]"
created: 2026-03-11
---

# Implement branch-based task scoping

Implement the branch scoping design from `artifacts/specs/branch-based-task-scoping.md` (task 0094). This adds a `branch` frontmatter field so tasks can be scoped to a git branch, and agents in worktrees only see relevant tasks.

## Requirements

1. **`branch` field in `create`** — Add `--branch <name>` flag to `openstation create`. `--branch auto` detects current branch via `git branch --show-current`. No flag = no `branch` field (global task).

2. **Branch filtering in `discover_tasks()`** — Add optional `branch` parameter. When `None` (default), no filtering. When set, a task is visible when its `branch` is empty OR matches the parameter.

3. **`list` branch filter** — Add `--branch <name>` flag (opt-in). `--branch auto` detects current branch via git. No flag = show all tasks (no filtering). Detached HEAD / no git with `--branch auto` = skip filtering with stderr warning.

4. **`run` branch filter** — Same `--branch` flag as `list`. No flag = run any ready task.

5. **`show` has no branch flag** — Explicit lookups always work.

6. **`update` support** — `branch` field editable via `openstation update <task> branch:<value>`. Empty value clears it.

## Context

- Spec: `artifacts/specs/branch-based-task-scoping.md`
- Depends on: 0092 (worktree `find_root()` — done), 0094 (spec — done)

## Verification

- [ ] `openstation create "task" --branch feature/x` writes `branch: feature/x` in frontmatter
- [ ] `openstation create "task" --branch auto` detects current branch from git
- [ ] `openstation create "task"` (no flag) writes no `branch` field
- [ ] `openstation list` (no flag) shows all tasks regardless of branch
- [ ] `openstation list --branch feature/x` shows only matching + global tasks
- [ ] `openstation list --branch auto` detects current branch and filters
- [ ] `openstation run --branch auto` only picks up matching + global ready tasks
- [ ] `openstation run` (no flag) picks up any ready task
- [ ] `openstation show` works regardless of branch
- [ ] `--branch auto` on detached HEAD skips filtering with warning
- [ ] `--branch auto` without git skips filtering with warning
- [ ] Tests cover all filtering scenarios
- [ ] Existing tests still pass
