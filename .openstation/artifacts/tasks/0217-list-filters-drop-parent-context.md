---
kind: task
name: 0217-list-filters-drop-parent-context
type: bug
status: done
assignee: developer
owner: user
created: 2026-03-22
---

# List Filters Drop Parent Context For Matching Children

## Requirements

`pull_in_subtasks()` in `tasks.py` only pulls *descendants* of matched tasks into the result set. It never pulls *ancestors*. When a filter matches a child (e.g., `--assignee developer` matches 0013), its parent (0010) is excluded, and `group_tasks_for_display` renders the child as a top-level task with no tree context.

1. Add a `pull_in_ancestors()` function in `tasks.py` that, for every task in the filtered set, walks the `parent` chain and includes any missing ancestors from `all_tasks`.
2. Call `pull_in_ancestors()` in `cmd_list` after the existing `pull_in_subtasks()` call (line 459), so the result set includes both descendants and ancestors of matched tasks.
3. Ancestor tasks pulled in for context only — they should still appear in the table (not be hidden), showing their actual status/assignee so the user can see where the child sits in the tree.
4. Do **not** change `pull_in_subtasks`, `group_tasks_for_display`, or `format_table` — the tree rendering already handles arbitrary depth correctly once all nodes are present.

## Verification

- [x] `pull_in_ancestors` function exists in `tasks.py`
- [x] `openstation list --assignee developer` on a vault with parent 0010 and child 0013 (assignee=developer) shows both 0010 and 0013, with 0013 indented under 0010
- [x] `openstation list --status review` on a vault where a child is in review but its parent is in-progress shows the parent for context
- [x] Filtering by status/assignee/type still excludes non-matching tasks that are not ancestors or descendants of matches
- [x] Tests cover: ancestor pull-in with single parent, multi-level ancestry, no-parent tasks unaffected

## Verification Report

*Verified: 2026-03-23*

| # | Criterion | Result | Evidence |
|---|-----------|--------|----------|
| 1 | `pull_in_ancestors` function exists in `tasks.py` | PASS | Function defined at line 263 in `tasks.py`, walks parent chain and appends missing ancestors |
| 2 | `--assignee developer` shows parent 0010 and child 0013 indented | PASS | `test_single_parent_pulled_in` creates 0010-parent (architect) + 0013-child (developer), asserts both present and child has `└─` prefix |
| 3 | `--status review` shows in-progress parent for context | PASS | `test_ancestor_shows_actual_status` creates parent (in-progress) + child (review), asserts parent line contains "in-progress" |
| 4 | Non-ancestor/non-descendant tasks still excluded | PASS | `test_non_ancestor_non_descendant_excluded` asserts 0003-unrelated is absent from output |
| 5 | Tests cover: single parent, multi-level, no-parent unaffected | PASS | `TestListAncestorPullIn` has 5 tests covering all cases; 2 existing tests updated to verify new behavior |

### Summary

5 passed, 0 failed. All verification criteria met. No changes to `pull_in_subtasks`, `group_tasks_for_display`, or `format_table` (confirmed via diff). Note: pytest execution was blocked by approval gate during verification; evidence based on code inspection and diff analysis.

## Progress

### 2026-03-23 — developer
> time: 16:02

Implemented pull_in_ancestors() in tasks.py, updated cmd_list to call it after pull_in_subtasks. Updated 2 existing tests, added 5 new tests in TestListAncestorPullIn. All 281 tests pass.

## Findings

Added `pull_in_ancestors()` in `tasks.py` (after `pull_in_subtasks`). The function builds a name→task lookup from `all_tasks`, then for each task in the filtered set walks the `parent` chain upward, appending any missing ancestors. Called in `cmd_list` on line 460, right after `pull_in_subtasks`.

No changes to `pull_in_subtasks`, `group_tasks_for_display`, or `format_table` — the existing tree renderer handles it once all nodes are present.

Updated two existing tests that expected parents to be excluded when only children matched (`test_orphan_subtask_shown_as_top_level` → `test_child_match_pulls_in_parent_for_context`, `test_assignee_filter_with_grouped_view` → `test_assignee_filter_pulls_in_parent_for_context`). Added `TestListAncestorPullIn` class with 5 tests: single parent, multi-level ancestry, no-parent unaffected, ancestor shows actual status, non-ancestor/non-descendant excluded. All 281 tests pass.
