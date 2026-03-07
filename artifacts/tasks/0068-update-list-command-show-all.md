---
kind: task
name: 0068-update-list-command-show-all
status: done
assignee: developer
owner: user
created: 2026-03-06
---

# Update List Command — Subtask Pull-In and Positional Filter

## Requirements

1. **Subtask pull-in rule** — for every task that matches the
   active filters (status, assignee), include all its subtasks
   (direct + nested descendants) in the output, regardless of
   whether those subtasks match the filters.

2. **Positional filter argument** — `openstation list [filter]`
   accepts an optional positional arg:
   - **Task ID/slug** (starts with digit) → show that task + all
     its subtasks, combined with `--status`/`--assignee` flags.
     Use `resolve_task()` for resolution.
   - **Agent/assignee name** (non-numeric) → equivalent to
     `--assignee <name>`.

3. **No breaking changes** — `--status` and `--assignee` flags
   still work; positional filter is additive.

4. **Current grouping/display preserved** — subtasks render with
   `└─` prefix under their parent, sorted by ID.

## Implementation Notes

- Modify `cmd_list()` in `bin/openstation` to implement pull-in
  logic after filtering: collect parent names from filtered set,
  then add their descendants from the full task list.
- Add `filter` positional argument to the `list` subparser
  (`nargs="?"`, default `None`). Auto-detect task vs assignee
  by checking if value starts with a digit.
- Update `group_tasks_for_display()` or post-filter logic as
  needed.
- Add tests in `tests/test_cli.py`.

## Verification

- [ ] `openstation list` (default active) shows subtasks of matching tasks even if subtask status is `done`/`failed`/`backlog`
- [ ] `openstation list 0055` shows task 0055 and all its subtasks
- [ ] `openstation list researcher` filters by assignee (same as `--assignee researcher`)
- [ ] Subtasks still display with `└─` prefix and correct grouping
- [ ] A task with no parent that doesn't match filters is still excluded
- [ ] Existing tests still pass
- [ ] New tests cover: pull-in behavior, positional task filter, positional assignee filter
