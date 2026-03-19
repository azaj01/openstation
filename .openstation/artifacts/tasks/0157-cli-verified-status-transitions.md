---
kind: task
name: 0157-cli-verified-status-transitions
type: implementation
status: done
assignee: developer
owner: user
parent: "[[0155-add-verified-status-to-lifecycle]]"
created: 2026-03-17
---

# CLI: `verified` Status Transitions

Implement `verified` as a valid status in the CLI transition
logic.

## Context

Depends on 0156 (docs) for the authoritative transition rules.
Read `docs/lifecycle.md` for the updated state machine before
implementing.

## Requirements

1. **Status transitions** — allow:
   - `review → verified`
   - `verified → done`
   - `verified → failed`
   - Block `review → done` (must go through `verified`)

2. **`openstation list`** — `--status verified` works as a
   filter.

3. **Sub-task parent auto-promotion** — `verified` ranks between
   `review` and `done`. A `verified` sub-task auto-promotes
   parent to at least `in-progress` (same rule as `review`).

4. **`openstation status` command** — validates the new
   transitions, rejects invalid ones with clear error messages
   (e.g., "task is in review — run verification first before
   marking done").

5. **Tests** — update existing transition tests, add new tests
   for `verified` transitions and rejection of `review → done`.

## Findings

Implemented `verified` as a valid CLI status across 3 source files
and 1 test file:

**`src/openstation/core.py`** — Updated lifecycle constants:
- `VALID_TRANSITIONS`: replaced `review→done` with `review→verified`,
  `verified→done`, `verified→failed`
- `VALID_STATUSES`: added `verified`
- `_STATUS_RANK`: inserted `verified` at rank 4 (between `review:3`
  and `done:5`)
- `_MIN_PARENT_STATUS`: added `verified → in-progress`

**`src/openstation/cli.py`** — Updated `--status` help text to
include `verified` in the status list and active filter description.

**`src/openstation/tasks.py`** — Two changes:
- Active filter now includes `verified` alongside `ready`,
  `in-progress`, `review`
- Custom error for `review → done` with hint to run verification
  first (includes `--verify` command suggestion)

**`tests/test_cli.py`** — Updated and added tests:
- Updated `test_status_all_valid_transitions` path to go through
  `verified`
- Updated `test_list_default_shows_only_active` to include verified
- Added `TestVerifiedStatusTransitions` (8 tests): transitions,
  blocking, error messages, list filtering, file content
- Added `TestVerifiedParentAutoPromotion` (2 tests): promotion and
  no-op when parent already ahead

All 264 tests pass.

## Progress

- 2026-03-17: Implemented verified status in CLI (core constants,
  transitions, list filter, error message, 10 new tests). All 264
  tests pass.

## Verification

- [x] `openstation status <task> verified` works from `review`
- [x] `openstation status <task> done` works from `verified`
- [x] `openstation status <task> done` rejects tasks in `review`
- [x] `openstation list --status verified` filters correctly
- [x] Sub-task parent auto-promotion handles `verified`
- [x] Error message for `review → done` mentions verification
- [x] Tests cover all new transitions
