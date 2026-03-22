---
kind: task
name: 0217-list-filters-drop-parent-context
type: bug
status: ready
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

- [ ] `pull_in_ancestors` function exists in `tasks.py`
- [ ] `openstation list --assignee developer` on a vault with parent 0010 and child 0013 (assignee=developer) shows both 0010 and 0013, with 0013 indented under 0010
- [ ] `openstation list --status review` on a vault where a child is in review but its parent is in-progress shows the parent for context
- [ ] Filtering by status/assignee/type still excludes non-matching tasks that are not ancestors or descendants of matches
- [ ] Tests cover: ancestor pull-in with single parent, multi-level ancestry, no-parent tasks unaffected
