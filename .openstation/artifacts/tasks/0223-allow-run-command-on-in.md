---
kind: task
name: 0223-allow-run-command-on-in
type: feature
status: done
assignee: developer
owner: user
created: 2026-03-23
---

# Allow Run Command On In-Progress Tasks

## Requirements

1. `openstation run --task <id>` must accept tasks with status `in-progress` in addition to `ready` — without requiring `--force`.
2. The status check in `run.py` (`assert_task_ready`) should treat both `ready` and `in-progress` as valid statuses for execution.
3. When a task is `in-progress`, the run command should **not** auto-transition it to `in-progress` again (idempotent — skip the transition if already in that status).
4. The `--force` flag continues to bypass all status checks as before.
5. Error messages should be updated to say `(expected 'ready' or 'in-progress')`.
6. Agent-mode (`openstation run <agent>`) should also discover `in-progress` tasks assigned to that agent (in addition to `ready` ones).

## Findings

### Changes Made

**`src/openstation/tasks.py`:**
- Renamed `assert_task_ready()` → `assert_task_runnable()` — now accepts both `ready` and `in-progress` statuses
- Renamed `find_ready_subtasks()` → `find_runnable_subtasks()` — subtask discovery now includes `in-progress` subtasks alongside `ready` ones
- Added comma-separated status support to `openstation list --status` filter (e.g., `--status ready,in-progress`)

**`src/openstation/run.py`:**
- Updated call sites to use renamed functions
- Error message now says `(expected 'ready' or 'in-progress')`
- UX messages changed from "ready subtask(s)" to "runnable subtask(s)"

**`.openstation/skills/openstation-execute/SKILL.md`:**
- Updated agent discovery command to `openstation list --status ready,in-progress --assignee <name>`
- Updated fallback scan instructions to match both statuses
- Added preference for `in-progress` over `ready` when multiple tasks exist

**`tests/test_cli.py`:**
- `test_task_in_progress_accepted` — verifies `in-progress` tasks run without `--force`
- `test_task_not_runnable` — verifies `review` status is still rejected
- `test_task_backlog_rejected` / `test_task_done_rejected` — verifies non-runnable statuses rejected
- `test_task_not_runnable_with_force` — verifies `--force` still bypasses checks
- `test_subtask_in_progress_collected` — verifies in-progress subtasks are discovered
- Updated all assertions referencing "ready subtask" → "runnable subtask"

### Design Decisions

- The run command does not auto-transition tasks — the agent handles that via the execute skill, which already checks current status before transitioning. Requirement 3 is satisfied naturally.
- Renamed functions to `*_runnable` rather than `*_ready_or_in_progress` for cleaner API naming.

## Verification

- [x] `openstation run --task <id>` succeeds when task status is `in-progress` (no `--force` needed)
- [x] `openstation run --task <id>` still succeeds when task status is `ready`
- [x] `openstation run --task <id>` still rejects tasks in `backlog`, `review`, `done`, `rejected` without `--force`
- [x] Error message mentions both `ready` and `in-progress` as expected statuses
- [x] `--force` still bypasses all status checks
- [x] Unit tests cover the new `in-progress` acceptance path
- [x] Agent-mode run discovers `in-progress` tasks

## Verification Report

*Verified: 2026-03-23*

| # | Criterion | Result | Evidence |
|---|-----------|--------|----------|
| 1 | `run --task` succeeds on `in-progress` | PASS | `assert_task_runnable()` (tasks.py:123-131) returns `True` for `in-progress`; test `test_task_in_progress_accepted` confirms exit 0 |
| 2 | `run --task` still succeeds on `ready` | PASS | `assert_task_runnable()` accepts both `ready` and `in-progress`; existing `ready` tests remain in the suite |
| 3 | Rejects `backlog`, `review`, `done`, `rejected` | PASS | `assert_task_runnable()` only allows `ready`/`in-progress`; tests `test_task_not_runnable`, `test_task_backlog_rejected`, `test_task_done_rejected` all assert exit 5 |
| 4 | Error message mentions both statuses | PASS | run.py:665 emits `"expected 'ready' or 'in-progress'"`; three tests assert this string |
| 5 | `--force` bypasses checks | PASS | run.py:662 skips `assert_task_runnable` when `force=True`; test `test_task_not_runnable_with_force` confirms exit 0 on `review` status |
| 6 | Unit tests cover `in-progress` path | PASS | 6 tests: `test_task_in_progress_accepted`, `test_task_not_runnable`, `test_task_backlog_rejected`, `test_task_done_rejected`, `test_task_not_runnable_with_force`, `test_subtask_in_progress_collected` |
| 7 | Agent-mode discovers `in-progress` tasks | PASS | SKILL.md updated: discovery command is `openstation list --status ready,in-progress --assignee <name>`; fallback scan checks both statuses; `find_runnable_subtasks()` includes `in-progress` (tasks.py:118) |

### Summary

7 passed, 0 failed. All verification criteria met.
