---
kind: task
name: 0116-add-ag-alias-for-agents
type: feature
status: done
assignee: developer
owner: user
parent: "[[0111-cli-expand-agents-command-with]]"
created: 2026-03-12
---

# Agents subcommand improvements

## Requirements

1. **`ag` alias** — register `ag` as an argparse alias for
   `agents` so all sub-actions work with the shorter name
   (`openstation ag list`, `openstation ag show architect`, etc.)

2. **`dispatch --dangerously-skip-permissions`** — add a
   `--dangerously-skip-permissions` flag to `agents dispatch`
   (default: off). Pass it through to `claude --agent <name>
   --dangerously-skip-permissions` when set. This is needed for
   agents like `project-manager` that require it.

## Verification

- [x] `openstation ag list` works (alias for `agents list`)
- [x] `openstation ag show <name>` works
- [x] `openstation agents` still works (canonical name unchanged)
- [x] Tests cover the `ag` alias (3 tests in `TestAgAlias`)

> **Note:** `dispatch` criteria removed — `agents dispatch` was
> intentionally removed per task 0120. `--dangerously-skip-permissions`
> lives on `openstation run` instead.
