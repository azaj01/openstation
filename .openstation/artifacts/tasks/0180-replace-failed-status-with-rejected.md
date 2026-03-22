---
kind: task
name: 0180-replace-failed-status-with-rejected
type: feature
status: done
assignee: developer
owner: user
created: 2026-03-20
---

# Replace `failed` with `rejected` in task lifecycle

Replace the `failed` terminal status with `rejected`. A task is
`rejected` when it won't be completed — whether descoped, never
started, superseded, or abandoned mid-effort.

## Requirements

1. **`core.py`** — Replace `failed` with `rejected` everywhere:
   - `VALID_STATUSES`: swap `failed` for `rejected`
   - `VALID_TRANSITIONS`: replace all `failed` transitions with:
     `backlog → rejected`, `ready → rejected`,
     `in-progress → rejected`, `review → rejected`
   - `_STATUS_RANK`: replace `failed` entry with `rejected`
   - `_MIN_PARENT_STATUS`: update if `failed` is referenced
2. **`docs/lifecycle.md`** — Update status list, transition table,
   and any prose referencing `failed`. Explain `rejected` meaning.
3. **`docs/task.spec.md`** — Update valid statuses if listed.
4. **Migrate existing tasks** — Bulk rename `status: failed` →
   `status: rejected` across all 12 tasks in `artifacts/tasks/`.
5. **Tests** — Update any tests referencing `failed` status.

## Findings

Replaced `failed` with `rejected` across the entire codebase:

- **`core.py`** — Updated `VALID_STATUSES`, `VALID_TRANSITIONS` (new: backlog/ready/in-progress/review → rejected; removed: verified → failed, failed → in-progress), `_STATUS_RANK`, `_MIN_PARENT_STATUS`, and `summary_block` parameter name.
- **`cli.py`** — Updated help text and status transition diagram in epilog.
- **`run.py`** — Renamed `failed_count` → `rejected_count` and updated summary output.
- **`docs/lifecycle.md`** — Rewrote transition table, status descriptions, guardrails, and ownership section.
- **`docs/task.spec.md`** — Updated status values table.
- **12 task files** — Migrated all `status: failed` → `status: rejected`.
- **`tests/test_cli.py`** — Updated 9 test methods; replaced `verified → failed` test with `verified → rejected` blocked test; added tests for all 4 new rejection transitions and `allowed_from("rejected")`.
- **`tests/test_hooks.py`** — Updated 2 hook matcher tests.
- **Commands** — Updated `openstation.reject.md` (now allows rejection from any active status), `openstation.list.md`, `openstation.update.md`.
- **Skills** — `openstation-execute/SKILL.md` already updated (reject table row, progress entry, verification section).

Key design change: `rejected` is now reachable from any pre-terminal status (backlog/ready/in-progress/review), not just review. The `verified → failed` and `failed → in-progress` rework transitions were removed — rejected is terminal.

## Verification

- [x] `VALID_STATUSES` contains `rejected`, not `failed`
- [x] `VALID_TRANSITIONS` allows `backlog/ready/in-progress/review → rejected`
- [x] No `failed` references remain in `core.py`, `lifecycle.md`, or `task.spec.md`
- [x] All 12 existing `status: failed` tasks migrated to `status: rejected`
- [x] Tests pass

## Verification Report

*Verified: 2026-03-20*

| # | Criterion | Result | Evidence |
|---|-----------|--------|----------|
| 1 | `VALID_STATUSES` contains `rejected`, not `failed` | PASS | `core.py:40` shows `{"backlog", "ready", "in-progress", "review", "verified", "done", "rejected"}` |
| 2 | `VALID_TRANSITIONS` allows `backlog/ready/in-progress/review → rejected` | PASS | `core.py:29,32,34,36` confirm all four transitions present |
| 3 | No `failed` references remain in `core.py`, `lifecycle.md`, or `task.spec.md` | PASS | Grep for `failed` returns zero matches in all three files |
| 4 | All 12 existing `status: failed` tasks migrated to `status: rejected` | PASS | Grep for `^status: failed` in `artifacts/tasks/` returns zero matches |
| 5 | Tests pass | PASS | 419 tests pass (`pytest tests/ -x -q` — 37s, zero failures) |

### Summary

5 passed, 0 failed. All verification criteria met.
